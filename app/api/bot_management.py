from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os

from app.core.database import get_db
from app.models.user import User, UserRole
from app.api.auth import get_current_teacher
from app.services.max_bot_client import MaxBotClient

router = APIRouter()


@router.get("/info")
async def get_bot_info(
    current_user: User = Depends(get_current_teacher)
):
    """Получение информации о боте"""
    try:
        bot = MaxBotClient()
        info = await bot.get_bot_info()
        await bot.close()
        return info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting bot info: {str(e)}")


@router.patch("/info")
async def update_bot_info(
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_teacher)
):
    """Обновление информации о боте"""
    try:
        bot = MaxBotClient()
        result = await bot.update_bot_info(name=name, description=description)
        await bot.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating bot info: {str(e)}")


@router.post("/send-message")
async def send_message(
    chat_id: str = Form(...),
    text: str = Form(...),
    format_type: str = Form("markdown"),
    current_user: User = Depends(get_current_teacher)
):
    """Отправка сообщения в чат"""
    if format_type not in ["markdown", "html"]:
        raise HTTPException(status_code=400, detail="Format must be 'markdown' or 'html'")
    
    try:
        bot = MaxBotClient()
        result = await bot.send_message(chat_id, text, format_type)
        await bot.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")


@router.post("/send-to-user")
async def send_message_to_user(
    user_id: str = Form(...),
    text: str = Form(...),
    format_type: str = Form("markdown"),
    current_user: User = Depends(get_current_teacher)
):
    """Отправка сообщения пользователю (создание приватного чата)"""
    if format_type not in ["markdown", "html"]:
        raise HTTPException(status_code=400, detail="Format must be 'markdown' or 'html'")
    
    try:
        bot = MaxBotClient()
        result = await bot.send_message_to_user(user_id, text, format_type)
        await bot.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message to user: {str(e)}")


@router.get("/chat/{chat_id}")
async def get_chat_info(
    chat_id: str,
    current_user: User = Depends(get_current_teacher)
):
    """Получение информации о чате"""
    try:
        bot = MaxBotClient()
        info = await bot.get_chat_info(chat_id)
        await bot.close()
        return info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat info: {str(e)}")


@router.get("/chat/{chat_id}/members")
async def get_chat_members(
    chat_id: str,
    current_user: User = Depends(get_current_teacher)
):
    """Получение списка участников чата"""
    try:
        bot = MaxBotClient()
        members = await bot.get_chat_members(chat_id)
        await bot.close()
        return members
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat members: {str(e)}")


@router.post("/chat/{chat_id}/members")
async def add_chat_member(
    chat_id: str,
    user_id: str = Form(...),
    current_user: User = Depends(get_current_teacher)
):
    """Добавление участника в чат"""
    try:
        bot = MaxBotClient()
        result = await bot.add_chat_member(chat_id, user_id)
        await bot.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding chat member: {str(e)}")


@router.delete("/chat/{chat_id}/members/{user_id}")
async def remove_chat_member(
    chat_id: str,
    user_id: str,
    current_user: User = Depends(get_current_teacher)
):
    """Удаление участника из чата"""
    try:
        bot = MaxBotClient()
        result = await bot.remove_chat_member(chat_id, user_id)
        await bot.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing chat member: {str(e)}")


@router.get("/chat/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_teacher)
):
    """Получение сообщений из чата"""
    if limit > 100:
        raise HTTPException(status_code=400, detail="Limit cannot exceed 100")
    
    try:
        bot = MaxBotClient()
        messages = await bot.get_messages(chat_id, limit, offset)
        await bot.close()
        return messages
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting messages: {str(e)}")


@router.put("/message/{message_id}")
async def edit_message(
    message_id: str,
    text: str = Form(...),
    format_type: str = Form("markdown"),
    current_user: User = Depends(get_current_teacher)
):
    """Редактирование сообщения"""
    if format_type not in ["markdown", "html"]:
        raise HTTPException(status_code=400, detail="Format must be 'markdown' or 'html'")
    
    try:
        bot = MaxBotClient()
        result = await bot.edit_message(message_id, text, format_type)
        await bot.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error editing message: {str(e)}")


@router.delete("/message/{message_id}")
async def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_teacher)
):
    """Удаление сообщения"""
    try:
        bot = MaxBotClient()
        result = await bot.delete_message(message_id)
        await bot.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting message: {str(e)}")


@router.get("/test-connection")
async def test_bot_connection(
    current_user: User = Depends(get_current_teacher)
):
    """Тестирование подключения к боту"""
    try:
        bot = MaxBotClient()
        info = await bot.get_bot_info()
        await bot.close()
        
        if "error" in info:
            return {
                "status": "error",
                "message": "Failed to connect to MAX API",
                "error": info["error"]
            }
        
        return {
            "status": "success",
            "message": "Successfully connected to MAX API",
            "bot_info": info
        }
    except ValueError as e:
        return {
            "status": "error",
            "message": "Bot token not configured",
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "Connection test failed",
            "error": str(e)
        } 