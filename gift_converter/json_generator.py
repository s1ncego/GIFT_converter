import json
from datetime import datetime
from typing import List
from gift_parser import Question

def question_to_dict(question: Question) -> dict:

    result = {
        "question_type": question.question_type,
        "text": question.text,
        "title": question.title
    }

    if question.question_type in ('single_choice', 'multiple_choice'):
        result["choices"] = [
            {
                "text": choice.text,
                "is_correct": choice.is_correct,
                "weight": choice.weight,
                "feedback": choice.feedback
            }
            for choice in question.choices
        ]

    elif question.question_type == 'short_answer':
        result["short_answers"] = [
            {
                "text": answer.text,
                "weight": answer.weight
            }
            for answer in question.short_answers
        ]

    elif question.question_type == 'matching':
        result["matching_pairs"] = [
            {
                "term": pair.term,
                "definition": pair.definition
            }
            for pair in question.matching_pairs
        ]

    return result

def save_to_json(questions: List[Question], output_path: str) -> None:
    data = {
        "metadata": {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "total_questions": len(questions)
        },
        "questions": [question_to_dict(q) for q in questions]
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Сохранено {len(questions)} вопросов -> {output_path}")