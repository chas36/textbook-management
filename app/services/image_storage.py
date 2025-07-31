import os
import uuid
from typing import List
from fastapi import UploadFile
from app.core.config import settings


def create_uploads_directory():
    """Создание директории для загрузок если не существует"""
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)


async def save_uploaded_file(file: UploadFile) -> str:
    """
    Сохранение загруженного файла
    Возвращает путь к сохраненному файлу
    """
    create_uploads_directory()
    
    # Генерируем уникальное имя файла
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(settings.UPLOADS_DIR, unique_filename)
    
    # Сохраняем файл
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return file_path


async def save_multiple_files(files: List[UploadFile]) -> List[str]:
    """
    Сохранение нескольких файлов
    Возвращает список путей к файлам
    """
    file_paths = []
    for file in files:
        file_path = await save_uploaded_file(file)
        file_paths.append(file_path)
    
    return file_paths


def get_file_url(file_path: str) -> str:
    """
    Получение URL для доступа к файлу
    """
    # В реальной реализации здесь будет URL до CDN или сервера
    return f"/static/uploads/{os.path.basename(file_path)}"