#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
Создает таблицы и первого пользователя-учителя
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import create_tables, SessionLocal
from app.models.user import User, UserRole
from app.api.auth import get_password_hash
from app.core.config import settings


def create_initial_teacher():
    """Создает первого учителя в системе"""
    db = SessionLocal()
    
    try:
        # Проверяем, есть ли уже учителя в системе
        existing_teacher = db.query(User).filter(User.role == UserRole.TEACHER).first()
        if existing_teacher:
            print("Учитель уже существует в системе")
            return
        
        # Создаем первого учителя
        teacher_password = "admin123"  # В продакшене использовать более сложный пароль
        hashed_password = get_password_hash(teacher_password)
        
        teacher = User(
            username="admin",
            email="admin@school.local",
            password_hash=hashed_password,
            role=UserRole.TEACHER,
            is_active=True
        )
        
        db.add(teacher)
        db.commit()
        
        print("✅ Первый учитель создан успешно!")
        print(f"Username: admin")
        print(f"Password: {teacher_password}")
        print("⚠️  Не забудьте изменить пароль после первого входа!")
        
    except Exception as e:
        print(f"❌ Ошибка при создании учителя: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Основная функция инициализации"""
    print("🚀 Инициализация системы управления учебниками...")
    
    try:
        # Создаем таблицы
        print("📋 Создание таблиц базы данных...")
        create_tables()
        print("✅ Таблицы созданы успешно!")
        
        # Создаем первого учителя
        print("👨‍🏫 Создание первого учителя...")
        create_initial_teacher()
        
        print("\n🎉 Инициализация завершена успешно!")
        print("Теперь вы можете запустить сервер командой: python main.py")
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 