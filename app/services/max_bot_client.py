import aiohttp
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

from app.core.config import settings


class MaxBotClient:
    def __init__(self, bot_token: Optional[str] = None):
        """
        Инициализация клиента МАКС бота
        
        Args:
            bot_token: Токен бота. Если не указан, берется из переменных окружения
        """
        self.bot_token = bot_token or os.getenv("MAX_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("Bot token is required. Set MAX_BOT_TOKEN environment variable or pass it to constructor.")
        
        self.base_url = "https://botapi.max.ru"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получение или создание HTTP сессии"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Выполнение HTTP запроса к API МАКС
        
        Args:
            method: HTTP метод (GET, POST, PUT, DELETE, PATCH)
            endpoint: Эндпоинт API
            data: Данные для отправки (для POST, PUT, PATCH)
        
        Returns:
            Ответ от API в виде словаря
        """
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}?access_token={self.bot_token}"
        
        try:
            if method.upper() == "GET":
                async with session.get(url) as response:
                    return await response.json()
            elif method.upper() == "POST":
                async with session.post(url, json=data) as response:
                    return await response.json()
            elif method.upper() == "PUT":
                async with session.put(url, json=data) as response:
                    return await response.json()
            elif method.upper() == "DELETE":
                async with session.delete(url) as response:
                    return await response.json()
            elif method.upper() == "PATCH":
                async with session.patch(url, json=data) as response:
                    return await response.json()
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        
        except aiohttp.ClientError as e:
            print(f"Error making request to MAX API: {e}")
            return {"error": str(e)}
    
    async def get_bot_info(self) -> Dict[str, Any]:
        """Получение информации о текущем боте"""
        return await self._make_request("GET", "/bots")
    
    async def update_bot_info(self, name: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        """Обновление информации о боте"""
        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        
        return await self._make_request("PATCH", "/bots", data)
    
    async def send_message(self, chat_id: str, text: str, format_type: str = "markdown") -> Dict[str, Any]:
        """
        Отправка сообщения в чат
        
        Args:
            chat_id: ID чата
            text: Текст сообщения
            format_type: Формат текста (markdown или html)
        """
        data = {
            "chat_id": chat_id,
            "body": {
                "text": text,
                "format": format_type
            }
        }
        
        return await self._make_request("POST", "/messages", data)
    
    async def send_message_to_user(self, user_id: str, text: str, format_type: str = "markdown") -> Dict[str, Any]:
        """
        Отправка сообщения пользователю (создание приватного чата)
        
        Args:
            user_id: ID пользователя
            text: Текст сообщения
            format_type: Формат текста (markdown или html)
        """
        # Сначала создаем приватный чат с пользователем
        chat_data = {
            "user_id": user_id
        }
        chat_response = await self._make_request("POST", "/chats", chat_data)
        
        if "error" in chat_response:
            return chat_response
        
        chat_id = chat_response.get("chat_id")
        if not chat_id:
            return {"error": "Failed to create chat"}
        
        # Отправляем сообщение в созданный чат
        return await self.send_message(chat_id, text, format_type)
    
    async def send_damage_notification(self, student_name: str, textbook_title: str, damage_type: str, is_during_check_period: bool) -> Dict[str, Any]:
        """Уведомление о повреждении учебника"""
        message = f"**Повреждение учебника**\n\n"
        message += f"👤 Ученик: {student_name}\n"
        message += f"📚 Учебник: {textbook_title}\n"
        message += f"🔧 Тип повреждения: {damage_type}\n"
        
        if is_during_check_period:
            message += f"✅ Сообщено в течение первой недели"
        else:
            message += f"⚠️ Сообщено после первой недели"
        
        # Отправляем уведомление учителю (нужно будет настроить chat_id учителя)
        teacher_chat_id = os.getenv("TEACHER_CHAT_ID")
        if teacher_chat_id:
            return await self.send_message(teacher_chat_id, message)
        else:
            print(f"Damage notification: {message}")
            return {"message": "Notification logged (teacher chat not configured)"}
    
    async def send_lost_notification(self, student_name: str, textbook_title: str, parent_phone: str) -> Dict[str, Any]:
        """Уведомление об утере учебника"""
        # Уведомление учителя
        teacher_message = f"**Утеря учебника**\n\n"
        teacher_message += f"👤 Ученик: {student_name}\n"
        teacher_message += f"📚 Учебник: {textbook_title}\n"
        teacher_message += f"📱 Телефон родителя: {parent_phone}"
        
        teacher_chat_id = os.getenv("TEACHER_CHAT_ID")
        if teacher_chat_id:
            await self.send_message(teacher_chat_id, teacher_message)
        
        # Уведомление родителя (если есть max_user_id)
        # TODO: Реализовать поиск пользователя по номеру телефона
        print(f"Lost notification to {parent_phone}: {teacher_message}")
        return {"message": "Lost notification sent"}
    
    async def send_found_notification(self, finder_name: str, textbook_title: str, found_location: str) -> Dict[str, Any]:
        """Уведомление о находке учебника"""
        message = f"**Найден учебник**\n\n"
        message += f"👤 Нашедший: {finder_name}\n"
        message += f"📚 Учебник: {textbook_title}\n"
        message += f"📍 Место находки: {found_location}"
        
        teacher_chat_id = os.getenv("TEACHER_CHAT_ID")
        if teacher_chat_id:
            return await self.send_message(teacher_chat_id, message)
        else:
            print(f"Found notification: {message}")
            return {"message": "Found notification logged"}
    
    async def send_parent_notification(self, parent_phone: str, student_name: str, message_type: str, **kwargs) -> Dict[str, Any]:
        """Уведомление родителей"""
        if message_type == "issue":
            message = f"**Выдача учебников**\n\n"
            message += f"👤 Ученик: {student_name}\n"
            message += f"📚 Количество: {kwargs.get('total_count', 0)} учебников\n\n"
            message += f"**Список учебников:**\n{kwargs.get('textbook_list', '')}"
        
        elif message_type == "return":
            message = f"**Возврат учебников**\n\n"
            message += f"👤 Ученик: {student_name}\n"
            message += f"📚 Количество: {kwargs.get('total_count', 0)} учебников\n\n"
            message += f"**Список учебников:**\n{kwargs.get('textbook_list', '')}"
        
        elif message_type == "lost":
            message = f"**Утеря учебника**\n\n"
            message += f"👤 Ученик: {student_name}\n"
            message += f"📚 Учебник: {kwargs.get('textbook_name', '')}\n"
            message += f"📅 Дата: {kwargs.get('lost_date', '')}\n\n"
            message += f"⚠️ Пожалуйста, помогите найти учебник"
        
        elif message_type == "found":
            message = f"**Найден учебник**\n\n"
            message += f"👤 Ученик: {student_name}\n"
            message += f"📚 Учебник: {kwargs.get('textbook_name', '')}\n"
            message += f"👥 Нашедший: {kwargs.get('finder_name', '')}\n\n"
            message += f"✅ Учебник найден и будет возвращен"
        
        elif message_type == "bulk_issue_summary":
            message = f"**Массовая выдача учебников**\n\n"
            message += f"👤 Ученик: {student_name}\n"
            message += f"📚 Количество: {kwargs.get('total_count', 0)} учебников\n\n"
            message += f"**Список учебников:**\n{kwargs.get('textbook_list', '')}"
        
        elif message_type == "return_reminder":
            message = f"**Напоминание о возврате**\n\n"
            message += f"👤 Ученик: {student_name}\n"
            message += f"📚 Количество: {kwargs.get('total_count', 0)} учебников\n\n"
            message += f"**Список учебников для возврата:**\n{kwargs.get('textbook_list', '')}\n\n"
            message += f"⚠️ Пожалуйста, напомните ребенку сдать учебники"
        
        elif message_type == "damage_check_reminder":
            message = f"**Проверка состояния учебников**\n\n"
            message += f"👤 Ученик: {student_name}\n"
            message += f"📚 Количество: {kwargs.get('textbook_count', 0)} учебников\n\n"
            message += f"⚠️ Не забудьте проверить состояние учебников в течение {kwargs.get('deadline_days', 7)} дней"
        
        else:
            message = f"**Уведомление**\n\n"
            message += f"👤 Ученик: {student_name}\n"
            message += f"📝 Тип: {message_type}"
        
        # TODO: Реализовать отправку родителям по номеру телефона
        # Пока просто логируем
        print(f"Parent notification to {parent_phone}: {message}")
        return {"message": f"Parent notification logged for {parent_phone}"}
    
    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """Получение информации о чате"""
        return await self._make_request("GET", f"/chats/{chat_id}")
    
    async def get_chat_members(self, chat_id: str) -> Dict[str, Any]:
        """Получение списка участников чата"""
        return await self._make_request("GET", f"/chats/{chat_id}/members")
    
    async def add_chat_member(self, chat_id: str, user_id: str) -> Dict[str, Any]:
        """Добавление участника в чат"""
        data = {"user_id": user_id}
        return await self._make_request("POST", f"/chats/{chat_id}/members", data)
    
    async def remove_chat_member(self, chat_id: str, user_id: str) -> Dict[str, Any]:
        """Удаление участника из чата"""
        return await self._make_request("DELETE", f"/chats/{chat_id}/members/{user_id}")
    
    async def get_messages(self, chat_id: str, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Получение сообщений из чата"""
        return await self._make_request("GET", f"/messages?chat_id={chat_id}&limit={limit}&offset={offset}")
    
    async def edit_message(self, message_id: str, text: str, format_type: str = "markdown") -> Dict[str, Any]:
        """Редактирование сообщения"""
        data = {
            "body": {
                "text": text,
                "format": format_type
            }
        }
        return await self._make_request("PUT", f"/messages/{message_id}", data)
    
    async def delete_message(self, message_id: str) -> Dict[str, Any]:
        """Удаление сообщения"""
        return await self._make_request("DELETE", f"/messages/{message_id}")
    
    async def close(self):
        """Закрытие HTTP сессии"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close() 