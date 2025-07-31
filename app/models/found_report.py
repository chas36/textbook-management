from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class FoundStatus(str, Enum):
    FOUND = "found"           # Найден
    RETURNED = "returned"     # Возвращен
    VERIFIED = "verified"     # Проверен


class FoundReport(Base):
    __tablename__ = "found_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    textbook_id = Column(Integer, ForeignKey("textbooks.id"), nullable=False)
    finder_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Кто нашел
    
    finder_type = Column(String, nullable=False)  # "student" или "teacher"
    location = Column(Text)  # Где найдено
    notes = Column(Text)     # Дополнительные заметки
    
    status = Column(Enum(FoundStatus), default=FoundStatus.FOUND)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    textbook = relationship("Textbook", back_populates="found_reports")
    finder = relationship("User", back_populates="found_reports")
    
    def __repr__(self):
        return f"<FoundReport(id={self.id}, status='{self.status}')>"


# Добавим обратные связи
from app.models.textbook import Textbook
from app.models.user import User

Textbook.found_reports = relationship("FoundReport", back_populates="textbook")
User.found_reports = relationship("FoundReport", back_populates="finder")