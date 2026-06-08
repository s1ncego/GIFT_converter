import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass
class Choice:
    text: str
    is_correct: bool = False
    weight: float = 0.0
    feedback: Optional[str] = None

@dataclass
class ShortAnswer:
    text: str
    weight: float = 100.0

@dataclass
class MatchingPair:
    term: str
    definition: str

@dataclass
class Question:
    question_type: str
    text: str
    title: Optional[str] = None
    choices: List[Choice] = field(default_factory=list)
    short_answers: List[ShortAnswer] = field(default_factory=list)
    matching_pairs: List[MatchingPair] = field(default_factory=list)

def text_to_html(text: str) -> str:
    text = text.strip()
    if not text:
        return "<p></p>"
    if "<" in text and ">" in text:
        return text
    text = text.replace("\n", "<br>")
    return f"<p>{text}</p>"

def unescape_gift(text: str) -> str:
    result = text
    for char in ['{', '}', '=', '~', '#', ':', '@']:
        result = result.replace(f'\\{char}', char)
    result = result.replace('\\\\', '\\')
    return result

def remove_comments(content: str) -> str:

    lines = content.split('\n')
    result = []
    for line in lines:
        if not line.strip().startswith('//'):
            result.append(line)
    return '\n'.join(result)

class GiftParser:

    def __init__(self):
        self.errors = []
        self.warnings = []

    def parse_file(self, filepath: str) -> List[Question]:
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='cp1251') as f:
                content = f.read()
        return self.parse_string(content)

    def parse_string(self, content: str) -> List[Question]:
        self.errors = []
        self.warnings = []

        content = remove_comments(content)
        content = content.replace('\r\n', '\n').replace('\r', '\n')

        blocks = re.split(r'\n\s*\n', content)
        questions = []

        for idx, block in enumerate(blocks, 1):
            block = block.strip()
            if not block:
                continue
            try:
                question = self._parse_block(block, idx)
                if question:
                    questions.append(question)
            except Exception as e:
                self.errors.append({
                    "question_number": idx,
                    "error": str(e),
                    "raw": block[:80]
                })

        return questions

    def _parse_block(self, raw: str, num: int) -> Optional[Question]:

        title = None
        title_match = re.match(r'^::(.+?)::', raw, re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()
            raw = raw[title_match.end():].strip()

        answer_content, question_text = self._find_answer_block(raw)

        if answer_content is None:
            self.warnings.append({
                "question_number": num,
                "warning": "Не найден блок ответов {}"
            })
            return None

        question_text = unescape_gift(question_text.strip())
        question_html = text_to_html(question_text)

        q_type, choices, short_answers, matching_pairs = \
            self._parse_answers(answer_content.strip(), num)

        if q_type is None:
            return None

        return Question(
            question_type=q_type,
            text=question_html,
            title=title,
            choices=choices,
            short_answers=short_answers,
            matching_pairs=matching_pairs
        )

    def _find_answer_block(self, text: str) -> Tuple[Optional[str], str]:
        depth = 0
        start = -1
        i = 0

        while i < len(text):
            if text[i] == '\\' and i + 1 < len(text):
                i += 2
                continue
            if text[i] == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    content = text[start + 1:i]
                    before = text[:start]
                    return content, before
            i += 1

        return None, text

    def _parse_answers(
        self,
        content: str,
        num: int
    ) -> Tuple[Optional[str], List[Choice], List[ShortAnswer], List[MatchingPair]]:
        choices = []
        short_answers = []
        matching_pairs = []

        if not content:
            return None, choices, short_answers, matching_pairs

        if '->' in content:
            matching_pairs = self._parse_matching(content)
            return 'matching', choices, short_answers, matching_pairs

        parts = self._split_by_markers(content)

        if not parts:
            text = unescape_gift(content.strip())
            short_answers.append(ShortAnswer(text=text, weight=100.0))
            return 'short_answer', choices, short_answers, matching_pairs

        has_wrong = any(marker == '~' for marker, _ in parts)
        has_correct = any(marker == '=' for marker, _ in parts)

        if has_correct and not has_wrong:
            for marker, part_text in parts:
                text, weight, _ = self._parse_one_answer(part_text)
                short_answers.append(
                    ShortAnswer(text=text, weight=weight or 100.0)
                )
            return 'short_answer', choices, short_answers, matching_pairs

        has_weights = any(re.search(r'%[-\d.]+%', p) for _, p in parts)
        correct_count = sum(1 for m, _ in parts if m == '=')

        for marker, part_text in parts:
            text, weight, feedback = self._parse_one_answer(part_text)
            text_html = text_to_html(text)

            if marker == '=':
                is_correct = True
                final_weight = weight if weight is not None else 100.0
            else:
                if weight is not None and weight > 0:
                    is_correct = True
                else:
                    is_correct = False
                final_weight = weight if weight is not None else 0.0

            choices.append(Choice(
                text=text_html,
                is_correct=is_correct,
                weight=final_weight,
                feedback=text_to_html(feedback) if feedback else None
            ))

        if has_weights or correct_count > 1:
            q_type = 'multiple_choice'
        else:
            q_type = 'single_choice'

        return q_type, choices, short_answers, matching_pairs

    def _split_by_markers(self, content: str) -> List[Tuple[str, str]]:
        parts = []
        current_marker = None
        current_chars = []
        i = 0

        while i < len(content):
            if content[i] == '\\' and i + 1 < len(content):
                if current_marker is not None:
                    current_chars.append(content[i:i+2])
                i += 2
                continue

            if content[i] in ('=', '~'):
                if current_marker is not None:
                    parts.append(
                        (current_marker, ''.join(current_chars).strip())
                    )
                    current_chars = []
                current_marker = content[i]
            else:
                if current_marker is not None:
                    current_chars.append(content[i])
            i += 1

        if current_marker and current_chars:
            parts.append((current_marker, ''.join(current_chars).strip()))

        return parts

    def _parse_one_answer(
        self,
        text: str
    ) -> Tuple[str, Optional[float], Optional[str]]:
        
        text = text.strip()
        weight = None
        feedback = None

        weight_match = re.match(r'^%(-?\d+(?:\.\d+)?)%', text)
        if weight_match:
            weight = float(weight_match.group(1))
            text = text[weight_match.end():].strip()

        parts = re.split(r'(?<!\\)#', text, maxsplit=1)
        if len(parts) == 2:
            text = parts[0].strip()
            feedback = unescape_gift(parts[1].strip()) or None

        text = unescape_gift(text)
        return text, weight, feedback

    def _parse_matching(self, content: str) -> List[MatchingPair]:
        pairs = []
        lines = content.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('='):
                line = line[1:].strip()
            if '->' not in line:
                continue
            parts = line.split('->', 1)
            if len(parts) == 2:
                term = unescape_gift(parts[0].strip())
                definition = unescape_gift(parts[1].strip())
                pairs.append(MatchingPair(
                    term=text_to_html(term),
                    definition=text_to_html(definition)
                ))

        return pairs