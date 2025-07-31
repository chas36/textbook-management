from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from typing import List


class TransactionType(str, Enum):
    ISSUE = "issue"      # Выдача
    RETURN = "return"    # Возврат


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    textbook_id = Column(Integer, ForeignKey("textbooks.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Кто совершил операцию
    
    type = Column(Enum(TransactionType), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    
    condition_before = Column(Text)  # Состояние до операции
    condition_after = Column(Text)   # Состояние после операции
    
    # Фото (пути к файлам)
    photo_paths = Column(Text)  # JSON строка с путями к фото
    
    notes = Column(Text)  # Дополнительные заметки
    
    # Связи
    textbook = relationship("Textbook", back_populates="transactions")
    student = relationship("Student", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, type='{self.type}', date='{self.date}')>"


# Добавим обратные связи в другие модели
from app.models.textbook import Textbook
from app.models.student import Student
from app.models.user import User

Textbook.transactions = relationship("Transaction", back_populates="textbook")
Student.transactions = relationship("Transaction", back_populates="student")
User.transactions = relationship("Transaction", back_populates="user")