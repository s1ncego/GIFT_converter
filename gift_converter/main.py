import sys
import os
import io
import zipfile
from gift_parser import GiftParser
from json_generator import save_to_json

TESTS_DIR = "tests"
RESULTS_DIR = "results"


def convert_single_file(input_path: str, output_path: str) -> None:

    if not os.path.exists(input_path):
        print(f"Ошибка: файл не найден -> {input_path}")
        return

    parser = GiftParser()

    if input_path.endswith('.zip'):
        with open(input_path, 'rb') as f:
            content_bytes = f.read()

        try:
            zip_buffer = io.BytesIO(content_bytes)
            zip_file = zipfile.ZipFile(zip_buffer, 'r')
        except zipfile.BadZipFile:
            print(f"Ошибка: повреждённый ZIP файл")
            return

        gift_names = [n for n in zip_file.namelist() if n.endswith('.gift')]
        if not gift_names:
            print(f"Ошибка: в ZIP не найден .gift файл")
            return

        print(f"  Найден GIFT файл в архиве: {gift_names[0]}")
        print(f"  Файлы в архиве: {zip_file.namelist()}")

        gift_bytes = zip_file.read(gift_names[0])
        content = _decode_content(gift_bytes)
        questions = parser.parse_string(content, zip_file=zip_file)
        zip_file.close()

    elif input_path.endswith(('.gift', '.txt')):
        try:
            with open(input_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(input_path, 'r', encoding='cp1251') as f:
                content = f.read()
        questions = parser.parse_string(content)

    else:
        print(f"Ошибка: неподдерживаемый формат файла")
        return

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


def _decode_content(content_bytes: bytes) -> str:
    for encoding in ['utf-8-sig', 'utf-8', 'cp1251']:
        try:
            return content_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Не удалось прочитать файл")


def convert_all_files() -> None:

    os.makedirs(RESULTS_DIR, exist_ok=True)

    all_files = [
        f for f in os.listdir(TESTS_DIR)
        if f.endswith('.gift') or f.endswith('.txt') or f.endswith('.zip')
    ]

    if not all_files:
        print(f"В папке {TESTS_DIR} нет файлов.")
        return

    for filename in all_files:
        name_without_ext = os.path.splitext(filename)[0]
        input_path = os.path.join(TESTS_DIR, filename)
        output_path = os.path.join(RESULTS_DIR, f"{name_without_ext}.json")

        print(f"Обрабатываю: {filename}")
        convert_single_file(input_path, output_path)
        print()


def main():
    if len(sys.argv) == 3:
        input_path = sys.argv[1]
        output_json = sys.argv[2]

        output_dir = os.path.dirname(output_json)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        convert_single_file(input_path, output_json)
    else:
        convert_all_files()


if __name__ == "__main__":
    main()