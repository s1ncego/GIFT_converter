import zipfile
import os
from PIL import Image
import io

def create_test_zip():
    
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes = img_bytes.getvalue()
    
    gift_content = """::Вопрос с картинкой::<p>Что изображено на картинке?</p>
    <img src="@@PLUGINFILE@@/test_image.png">{
    =Красный квадрат
    ~Синий круг
    ~Зелёный треугольник
    }

    ::Вопрос без картинки::Сколько будет 2+2?{
    =4
    ~3
    ~5
    }"""
        
    with zipfile.ZipFile('tests/test_with_image.zip', 'w') as zf:
        zf.writestr('questions.gift', gift_content.encode('utf-8'))
        zf.writestr('files/test_image.png', img_bytes)
    
    print("Создан tests/test_with_image.zip")

if __name__ == "__main__":
    create_test_zip()