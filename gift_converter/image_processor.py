import base64
import re
import zipfile
from typing import Optional

SUPPORTED_FORMATS = {
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'svg': 'image/svg+xml'
}

MAX_IMAGE_SIZE = 2 * 1024 * 1024   # 2 МБ на один файл
MAX_ZIP_SIZE = 50 * 1024 * 1024    # 50 МБ на весь архив

PLUGINFILE_PATTERN = r'@@PLUGINFILE@@/([^\s"\'\\<>]+)'

def process_images_in_text(
    text: str,
    zip_file: Optional[zipfile.ZipFile] = None
) -> str:
    """
    Находит @@PLUGINFILE@@/img.png в тексте,
    берёт файл из zip, конвертирует в base64.
    Если картинка уже в base64 — не трогает.
    """

    if '@@PLUGINFILE@@' not in text:
        return text

    if zip_file is None:
        raise ValueError(
            "Найдена ссылка @@PLUGINFILE@@, но ZIP архив не передан"
        )

    def replacer(match):
        filename = match.group(1)
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''

        if ext not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Файл '{filename}': формат .{ext} не поддерживается. "
                f"Поддерживаются: {', '.join(SUPPORTED_FORMATS.keys())}"
            )

        found_path = None
        for name in zip_file.namelist():
            if name.endswith(filename):
                found_path = name
                break

        if not found_path:
            raise FileNotFoundError(
                f"Файл '{filename}' не найден в архиве"
            )

        info = zip_file.getinfo(found_path)
        if info.file_size > MAX_IMAGE_SIZE:
            size_mb = info.file_size / (1024 * 1024)
            raise ValueError(
                f"Файл '{filename}' слишком большой: "
                f"{size_mb:.1f} МБ (максимум 2 МБ)"
            )

        img_bytes = zip_file.read(found_path)
        b64 = base64.b64encode(img_bytes).decode('utf-8')
        mime = SUPPORTED_FORMATS[ext]

        return f'data:{mime};base64,{b64}'

    return re.sub(PLUGINFILE_PATTERN, replacer, text)


def validate_zip_size(content_bytes: bytes) -> None:
    """Проверяет размер zip архива"""
    size = len(content_bytes)
    if size > MAX_ZIP_SIZE:
        size_mb = size / (1024 * 1024)
        raise ValueError(
            f"ZIP архив слишком большой: "
            f"{size_mb:.1f} МБ (максимум 50 МБ)"
        )