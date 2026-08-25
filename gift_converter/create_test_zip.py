import zipfile
import io
import os
from PIL import Image


def create_test_image(color: str, size=(100, 100)) -> bytes:
    img = Image.new('RGB', size, color=color)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def create_large_image() -> bytes:
    img = Image.new('RGB', (2000, 2000), color='blue')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


os.makedirs('tests', exist_ok=True)


# Обычный ZIP с одной картинкой
with zipfile.ZipFile('tests/test_one_image.zip', 'w') as zf:
    gift = """::Вопрос с картинкой::<p>Что на картинке?</p>
<img src="@@PLUGINFILE@@/red.png">{
=Красный квадрат
~Синий круг
}"""
    zf.writestr('questions.gift', gift.encode('utf-8'))
    zf.writestr('files/red.png', create_test_image('red'))
print("test_one_image.zip")


# ZIP с несколькими картинками в одном вопросе
with zipfile.ZipFile('tests/test_multiple_images.zip', 'w') as zf:
    gift = """::Две картинки::<p>Картинка 1: <img src="@@PLUGINFILE@@/red.png"> Картинка 2: <img src="@@PLUGINFILE@@/blue.png"></p>{
=Ответ
}"""
    zf.writestr('questions.gift', gift.encode('utf-8'))
    zf.writestr('files/red.png', create_test_image('red'))
    zf.writestr('files/blue.png', create_test_image('blue'))
print("test_multiple_images.zip")


# ZIP с картинками в разных вопросах
with zipfile.ZipFile('tests/test_images_in_different_questions.zip', 'w') as zf:
    gift = """::Вопрос 1::<img src="@@PLUGINFILE@@/red.png"> Что это?{
=Красный
~Синий
}

::Вопрос 2::<img src="@@PLUGINFILE@@/blue.png"> Что это?{
=Синий
~Красный
}

::Вопрос без картинки::Сколько будет 2+2?{
=4
~3
}"""
    zf.writestr('questions.gift', gift.encode('utf-8'))
    zf.writestr('files/red.png', create_test_image('red'))
    zf.writestr('files/blue.png', create_test_image('blue'))
print("test_images_in_different_questions.zip")


# ZIP без картинок обычный GIFT в архиве
with zipfile.ZipFile('tests/test_no_images.zip', 'w') as zf:
    gift = """::Вопрос 1::Сколько будет 2+2?{
=4
~3
~5
}

::Вопрос 2::Столица России?{
=Москва
~Париж
}"""
    zf.writestr('questions.gift', gift.encode('utf-8'))
print("test_no_images.zip")


# Картинка лежит в подпапке внутри zip
with zipfile.ZipFile('tests/test_image_in_subfolder.zip', 'w') as zf:
    gift = """::Вопрос::<img src="@@PLUGINFILE@@/red.png">{=Ответ}"""
    zf.writestr('questions.gift', gift.encode('utf-8'))
    zf.writestr('media/subfolder/red.png', create_test_image('red'))
print("test_image_in_subfolder.zip")

# Неподдерживаемый формат файла (mp4)
with zipfile.ZipFile('tests/test_bad_format.zip', 'w') as zf:
    gift = """::Вопрос::<video src="@@PLUGINFILE@@/video.mp4">{=Ответ}"""
    zf.writestr('questions.gift', gift.encode('utf-8'))
    zf.writestr('files/video.mp4', b'fake video data')
print("test_bad_format.zip")


# Картинка есть в тексте но отсутствует в архиве
with zipfile.ZipFile('tests/test_missing_image.zip', 'w') as zf:
    gift = """::Вопрос::<img src="@@PLUGINFILE@@/missing.png">{=Ответ}"""
    zf.writestr('questions.gift', gift.encode('utf-8'))
print("test_missing_image.zip")


# Картинка больше 2 МБ
with zipfile.ZipFile('tests/test_large_image.zip', 'w') as zf:
    gift = """::Вопрос::<img src="@@PLUGINFILE@@/large.png">{=Ответ}"""
    zf.writestr('questions.gift', gift.encode('utf-8'))
    zf.writestr('files/large.png', create_large_image())
print("test_large_image.zip")


# ZIP без .gift файла внутри
with zipfile.ZipFile('tests/test_no_gift.zip', 'w') as zf:
    zf.writestr('files/red.png', create_test_image('red'))
    zf.writestr('readme.txt', b'no gift here')
print("test_no_gift.zip")


# Повреждённый ZIP
with open('tests/test_corrupted.zip', 'wb') as f:
    f.write(b'this is not a zip file at all')
print("test_corrupted.zip")

