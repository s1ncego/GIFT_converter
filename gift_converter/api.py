import json
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from gift_parser import GiftParser
from json_generator import question_to_dict
from gift_generator import load_questions_from_dict, questions_to_gift_string
from pydantic import BaseModel
from typing import List, Optional

class ChoiceSchema(BaseModel):
    text: str
    is_correct: bool
    weight: float
    feedback: Optional[str] = None

class ShortAnswerSchema(BaseModel):
    text: str
    weight: float

class MatchingPairSchema(BaseModel):
    term: str
    definition: str

class QuestionSchema(BaseModel):
    question_type: str
    text: str
    title: Optional[str] = None
    choices: Optional[List[ChoiceSchema]] = None
    short_answers: Optional[List[ShortAnswerSchema]] = None
    matching_pairs: Optional[List[MatchingPairSchema]] = None

class ConvertResponseSchema(BaseModel):
    created_at: str
    total_questions: int
    questions: List[QuestionSchema]

app = FastAPI(
    title="GIFT Converter API",
    version="1.0.0",
    #swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)


@app.get("/")
def root():
    return {
        "service": "GIFT Converter API",
        "version": "1.0.0",
        "endpoints": {
            "POST /gift-to-json": "конвертация GIFT файла в JSON",
            "POST /json-to-gift": "конвертация JSON в GIFT текст",
            "GET  /docs": "интерактивная дока"
        }
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/gift-to-json", response_model=ConvertResponseSchema)
async def gift_to_json(file: UploadFile = File(...)):
    if not file.filename.endswith(('.gift', '.txt')):
        raise HTTPException(status_code=400, detail="Нужен .gift или .txt файл")

    content_bytes = await file.read()

    content = None
    for encoding in ['utf-8-sig', 'utf-8', 'cp1251']:
        try:
            content = content_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        raise HTTPException(status_code=400, detail="Не удалось прочитать файл")

    parser = GiftParser()
    questions = parser.parse_string(content)

    return JSONResponse(content={
        "created_at": datetime.now().isoformat(),
        "total_questions": len(questions),
        "questions": [question_to_dict(q) for q in questions]
    })


@app.post("/json-to-gift")
async def json_to_gift(file: UploadFile = File(...)):
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Нужен .json файл")

    content_bytes = await file.read()

    try:
        data = json.loads(content_bytes.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Невалидный JSON")

    questions = load_questions_from_dict(data)
    gift_text = questions_to_gift_string(questions)

    return PlainTextResponse(content=gift_text)