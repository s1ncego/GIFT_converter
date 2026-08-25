import io
import json
import zipfile
from gift_parser import GiftParser
from json_generator import question_to_dict
from image_processor import validate_zip_size


def run_test(name, zip_path, expect_success, check_base64=False):
    print(name)
    try:
        with open(zip_path, 'rb') as f:
            content_bytes = f.read()

        validate_zip_size(content_bytes)

        zip_buffer = io.BytesIO(content_bytes)
        zip_file = zipfile.ZipFile(zip_buffer, 'r')

        gift_names = [n for n in zip_file.namelist() if n.endswith('.gift')]
        if not gift_names:
            raise FileNotFoundError("В ZIP не найден .gift файл")

        content = zip_file.read(gift_names[0]).decode('utf-8')

        parser = GiftParser()
        questions = parser.parse_string(content, zip_file=zip_file)
        zip_file.close()

        if parser.errors:
            raise ValueError(parser.errors[0]['error'])

        result_json = json.dumps(
            [question_to_dict(q) for q in questions],
            ensure_ascii=False
        )

        if expect_success:
            if check_base64:
                count = result_json.count('data:image')
                if count == 0:
                    print(f"  ПРОВАЛ - base64 не найден")
                    return False
                print(f"  успех, картинок: {count}")
            else:
                print(f"  успех, вопросов: {len(questions)}")
            return True
        else:
            print(f"  ПРОВАЛ - ожидалась ошибка")
            return False

    except Exception as e:
        if not expect_success:
            print(f"  успех, ошибка: {e}")
            return True
        else:
            print(f"  ПРОВАЛ - {e}")
            return False


def main():
    tests = [
        ("одна картинка",                  "tests/test_one_image.zip",                     True,  True),
        ("несколько картинок в вопросе",   "tests/test_multiple_images.zip",               True,  True),
        ("картинки в разных вопросах",     "tests/test_images_in_different_questions.zip", True,  True),
        ("zip без картинок",               "tests/test_no_images.zip",                     True,  False),
        ("картинка в подпапке",            "tests/test_image_in_subfolder.zip",            True,  True),
        ("неподдерживаемый формат",        "tests/test_bad_format.zip",                    False, False),
        ("картинка отсутствует в архиве",  "tests/test_missing_image.zip",                 False, False),
        ("zip без gift файла",             "tests/test_no_gift.zip",                       False, False),
        ("повреждённый zip",               "tests/test_corrupted.zip",                     False, False),
    ]

    passed = 0
    failed = 0

    for name, path, expect_success, check_base64 in tests:
        ok = run_test(name, path, expect_success, check_base64)
        if ok:
            passed += 1
        else:
            failed += 1

    print(f"\nрезультат: {passed} passed, {failed} failed")


if __name__ == "__main__":
    main()