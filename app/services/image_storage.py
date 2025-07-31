import os
import aiofiles
from fastapi import UploadFile, HTTPException
from typing import List
from app.core.config import settings
import uuid


class ImageStorage:
    def __init__(self):
        self.upload_dir = settings.UPLOADS_DIR
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Создает необходимые директории, если они не существуют"""
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def save_image(self, file: UploadFile, filename: str) -> str:
        """Сохраняет изображение и возвращает путь к файлу"""
        # Проверяем тип файла
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Проверяем размер файла (максимум 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        file_size = 0
        
        # Читаем файл и сохраняем его
        file_path = os.path.join(self.upload_dir, filename)
        
        async with aiofiles.open(file_path, 'wb') as f:
            while chunk := await file.read(8192):  # 8KB chunks
                file_size += len(chunk)
                if file_size > max_size:
                    # Удаляем частично сохраненный файл
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    raise HTTPException(status_code=400, detail="File too large (max 10MB)")
                await f.write(chunk)
        
        # Возвращаем относительный путь для сохранения в БД
        return f"/static/uploads/{filename}"
    
    async def delete_image(self, file_path: str) -> bool:
        """Удаляет изображение по пути"""
        if not file_path or not file_path.startswith('/static/uploads/'):
            return False
        
        # Извлекаем имя файла из пути
        filename = os.path.basename(file_path)
        full_path = os.path.join(self.upload_dir, filename)
        
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        
        return False
    
    async def delete_images(self, file_paths: List[str]) -> int:
        """Удаляет несколько изображений и возвращает количество удаленных"""
        deleted_count = 0
        for file_path in file_paths:
            if await self.delete_image(file_path):
                deleted_count += 1
        return deleted_count
    
    def get_image_url(self, file_path: str) -> str:
        """Возвращает полный URL для изображения"""
        if not file_path:
            return ""
        
        # Если путь уже полный URL, возвращаем как есть
        if file_path.startswith('http'):
            return file_path
        
        # Иначе добавляем базовый URL
        return f"http://localhost:8000{file_path}"
    
    def validate_image(self, file: UploadFile) -> bool:
        """Проверяет, является ли файл валидным изображением"""
        if not file.content_type:
            return False
        
        allowed_types = [
            'image/jpeg',
            'image/jpg', 
            'image/png',
            'image/gif',
            'image/webp'
        ]
        
        return file.content_type in allowed_types