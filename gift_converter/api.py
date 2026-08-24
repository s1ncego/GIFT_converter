import io
import json
import zipfile
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from gift_parser import GiftParser
from json_generator import question_to_dict
from gift_generator import load_questions_from_dict, questions_to_gift_string
from image_processor import validate_zip_size  # ← новый импорт
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

    content_bytes = await file.read()
    filename = file.filename.lower()

    if filename.endswith('.zip'):

        try:
            validate_zip_size(content_bytes)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        try:
            zip_buffer = io.BytesIO(content_bytes)
            zip_file = zipfile.ZipFile(zip_buffer, 'r')
        except zipfile.BadZipFile:
            raise HTTPException(status_code=400, detail="Повреждённый ZIP файл")

        gift_names = [n for n in zip_file.namelist() if n.endswith('.gift')]
        if not gift_names:
            raise HTTPException(status_code=400, detail="В ZIP не найден .gift файл")

        gift_bytes = zip_file.read(gift_names[0])
        content = _decode_content(gift_bytes)

        parser = GiftParser()
        questions = parser.parse_string(content, zip_file=zip_file)
        zip_file.close()

    elif filename.endswith(('.gift', '.txt')):
        content = _decode_content(content_bytes)
        parser = GiftParser()
        questions = parser.parse_string(content)

    else:
        raise HTTPException(
            status_code=400,
            detail="Нужен .gift, .txt или .zip файл"
        )

    return JSONResponse(content={
        "created_at": datetime.now().isoformat(),
        "total_questions": len(questions),
        "questions": [question_to_dict(q) for q in questions]
    })


def _decode_content(content_bytes: bytes) -> str:
    for encoding in ['utf-8-sig', 'utf-8', 'cp1251']:
        try:
            return content_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise HTTPException(status_code=400, detail="Не удалось прочитать файл")


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