# GIFT Converter API

## Описание

Сервис для конвертации тестовых вопросов между форматами GIFT и JSON, принимает файлы и возвращает результат конвертации.

Поддерживается конвертация в обе стороны:
- GIFT -> JSON
- JSON -> GIFT

## Технологии
Python 3.11 - FastAPI - Uvicorn 

## Структура проекта
- gift_converter/
    - api.py -- REST API, эндпоинты и обработка запросов
    - gift_parser.py -- парсер формата GIFT в объекты Python
    - gift_generator.py -- генератор GIFT текста из объектов Python
    - json_generator.py -- конвертер объектов Python в JSON
    - main.py -- запуск конвертации из командной строки
    - tests/ -- тестовые GIFT файлы
    - results/ -- тестовые JSON файлы

## Запуск

- pip install fastapi uvicorn python-multipart
- uvicorn api:app --host 0.0.0.0 --port 8000

- #дока для тестирования
http://<адрес_сервера>:8000/docs


| МЕТОД | ПУТЬ | ОПИСАНИЕ |
|---|---|---|
| GET | / | информация о сервисе |
| GET | /health | проверка работоспособности |
| POST | /gift-to-json | конвертация GIFT файла в JSON |
| POST | /json-to-gift | конвертация JSON файла в GIFT |