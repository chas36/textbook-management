"""
Клиент для работы с ботом МАКС
Заглушка для будущей интеграции
"""
from typing import Optional, Dict, Any
import httpx
from app.core.config import settings


class MaxBotClient:
    def __init__(self, bot_token: str = None):
        self.bot_token = bot_token
        self.base_url = "https://api.max-messenger.ru/v1"  # Пример URL
        self.client = httpx.AsyncClient()
    
    async def send_message(self, user_id: str, text: str, **kwargs) -> Dict[str, Any]:
        """
        Отправка сообщения пользователю
        """
        # В реальной реализации будет вызов API МАКС
        print(f"Отправка сообщения в МАКС: user_id={user_id}, text={text}")
        return {"status": "success", "message_id": "12345"}
    
    async def send_photo(self, user_id: str, photo_path: str, caption: str = None) -> Dict[str, Any]:
        """
        Отправка фото пользователю
        """
        print(f"Отправка фото в МАКС: user_id={user_id}, photo={photo_path}")
        return {"status": "success", "message_id": "12346"}
    
    async def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Получение информации о пользователе
        """
        return {
            "id": user_id,
            "first_name": "Имя",
            "last_name": "Фамилия",
            "username": "username"
        }
    
    async def close(self):
        """Закрытие соединения"""
        await self.client.aclose()


# Глобальный экземпляр клиента
max_bot_client = MaxBotClient()