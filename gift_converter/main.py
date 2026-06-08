import sys
import os
from gift_parser import GiftParser
from json_generator import save_to_json

TESTS_DIR = "tests"
RESULTS_DIR = "results"

def convert_single_file(input_path: str, output_path: str) -> None:

    if not os.path.exists(input_path):
        print(f"Ошибка: файл не найден -> {input_path}")
        return

    parser = GiftParser()
    questions = parser.parse_file(input_path)

    print(f"  Найдено вопросов: {len(questions)}")
    for i, question in enumerate(questions, 1):
        title = question.title or "Без названия"
        print(f"    {i}. [{question.question_type}] {title}")

    if parser.errors:
        print(f"  Ошибки парсинга ({len(parser.errors)}):")
        for err in parser.errors:
            print(f"    Блок {err['question_number']}: {err['error']}")

    if parser.warnings:
        print(f"  Предупреждения ({len(parser.warnings)}):")
        for w in parser.warnings:
            print(f"    Блок {w['question_number']}: {w['warning']}")

    if questions:
        save_to_json(questions, output_path)
    else:
        print(f"  Нет вопросов для сохранения.")

def convert_all_files() -> None:

    os.makedirs(RESULTS_DIR, exist_ok=True)

    gift_files = [
    f for f in os.listdir(TESTS_DIR)
    if f.endswith('.gift') or f.endswith('.txt')
    ]

    if not gift_files:
        print(f"В папке {TESTS_DIR} нет .gift файлов.")
        return

    for filename in gift_files:
        name_without_ext = os.path.splitext(filename)[0]

        input_path = os.path.join(TESTS_DIR, filename)
        output_path = os.path.join(RESULTS_DIR, f"{name_without_ext}.json")

        convert_single_file(input_path, output_path)
        print()

def main():

    if len(sys.argv) == 3:
        input_gift = sys.argv[1]
        output_json = sys.argv[2]

        output_dir = os.path.dirname(output_json)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        convert_single_file(input_gift, output_json)
    else:
        convert_all_files()

if __name__ == "__main__":
    main()


