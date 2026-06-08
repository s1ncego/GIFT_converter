import json
from typing import List
from gift_parser import Question, Choice, ShortAnswer, MatchingPair


def html_to_plain(text: str) -> str:
    if text is None:
        return ""
    return text.strip()


def escape_gift(text: str) -> str:
    result = text
    result = result.replace('\\', '\\\\')
    for char in ['{', '}', '~', '#', '=', ':', '@']:
        result = result.replace(char, f'\\{char}')
    return result


def question_to_gift(question: Question) -> str:
    lines = []

    title = question.title or ""
    text = html_to_plain(question.text)

    lines.append(f"::{title}::{text}{{")

    if question.question_type == 'single_choice':
        lines.extend(_choices_to_gift(question.choices))

    elif question.question_type == 'multiple_choice':
        lines.extend(_weighted_choices_to_gift(question.choices))

    elif question.question_type == 'short_answer':
        lines.extend(_short_answers_to_gift(question.short_answers))

    elif question.question_type == 'matching':
        lines.extend(_matching_to_gift(question.matching_pairs))

    lines.append("}")

    return "\n".join(lines)


def _choices_to_gift(choices: List[Choice]) -> List[str]:
    lines = []
    for choice in choices:
        text = html_to_plain(choice.text)
        marker = "=" if choice.is_correct else "~"
        feedback_str = ""
        if choice.feedback:
            feedback_text = html_to_plain(choice.feedback)
            feedback_str = f"#{feedback_text}"
        lines.append(f"{marker}{text}{feedback_str}")
    return lines


def _weighted_choices_to_gift(choices: List[Choice]) -> List[str]:
    lines = []
    for choice in choices:
        text = html_to_plain(choice.text)
        feedback_str = ""
        if choice.feedback:
            feedback_text = html_to_plain(choice.feedback)
            feedback_str = f"#{feedback_text}"

        weight = choice.weight
        if weight == int(weight):
            weight_str = str(int(weight))
        else:
            weight_str = str(weight)

        lines.append(f"~%{weight_str}%{text}{feedback_str}")
    return lines


def _short_answers_to_gift(answers: List[ShortAnswer]) -> List[str]:
    lines = []
    for answer in answers:
        text = answer.text.strip()
        lines.append(f"={text}")
    return lines


def _matching_to_gift(pairs: List[MatchingPair]) -> List[str]:
    lines = []
    for pair in pairs:
        term = html_to_plain(pair.term)
        definition = html_to_plain(pair.definition)
        lines.append(f"={term} -> {definition}")
    return lines


def questions_to_gift_string(questions: List[Question]) -> str:
    blocks = [question_to_gift(q) for q in questions]
    return "\n\n".join(blocks)


def load_questions_from_json(json_path: str) -> List[Question]:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    questions = []
    for item in data.get("questions", []):
        question = _dict_to_question(item)
        if question:
            questions.append(question)

    return questions


def load_questions_from_dict(data: dict) -> List[Question]:
    questions = []
    for item in data.get("questions", []):
        question = _dict_to_question(item)
        if question:
            questions.append(question)
    return questions


def _dict_to_question(item: dict) -> Question:

    q_type = item.get("question_type")
    text = item.get("text", "")
    title = item.get("title")

    choices = []
    short_answers = []
    matching_pairs = []

    if q_type in ('single_choice', 'multiple_choice'):
        for c in item.get("choices", []):
            choices.append(Choice(
                text=c.get("text", ""),
                is_correct=c.get("is_correct", False),
                weight=c.get("weight", 0.0),
                feedback=c.get("feedback")
            ))

    elif q_type == 'short_answer':
        for a in item.get("short_answers", []):
            short_answers.append(ShortAnswer(
                text=a.get("text", ""),
                weight=a.get("weight", 100.0)
            ))

    elif q_type == 'matching':
        for p in item.get("matching_pairs", []):
            matching_pairs.append(MatchingPair(
                term=p.get("term", ""),
                definition=p.get("definition", "")
            ))

    return Question(
        question_type=q_type,
        text=text,
        title=title,
        choices=choices,
        short_answers=short_answers,
        matching_pairs=matching_pairs
    )


def save_to_gift(questions: List[Question], output_path: str) -> None:

    content = questions_to_gift_string(questions)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Сохранено {len(questions)} вопросов -> {output_path}")