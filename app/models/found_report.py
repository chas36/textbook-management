from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class FoundStatus(str, enum.Enum):
    FOUND = "found"           # Найден
    RETURNED = "returned"     # Возвращен


class FoundReport(Base):
    __tablename__ = "found_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    textbook_id = Column(Integer, ForeignKey("textbooks.id"), nullable=False)
    found_location = Column(String, nullable=False)  # Где найдено
    description = Column(Text)  # Описание находки
    photos = Column(Text)  # JSON строка с путями к фото
    
    status = Column(Enum(FoundStatus), default=FoundStatus.FOUND)
    notes = Column(Text)  # Дополнительные заметки
    
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Кто сообщил
    returned_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Кто вернул
    
    found_at = Column(DateTime(timezone=True), server_default=func.now())
    returned_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<FoundReport(id={self.id}, status='{self.status}')>"