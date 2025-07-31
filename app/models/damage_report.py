from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class DamageType(str, enum.Enum):
    MINOR = "minor"          # Незначительные повреждения
    MODERATE = "moderate"    # Умеренные повреждения
    SEVERE = "severe"        # Серьезные повреждения
    LOST = "lost"           # Утерян


class DamageStatus(str, enum.Enum):
    PENDING = "pending"      # Ожидает проверки
    CHECKED = "checked"      # Проверен


class DamageReport(Base):
    __tablename__ = "damage_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    textbook_id = Column(Integer, ForeignKey("textbooks.id"), nullable=False)
    damage_type = Column(Enum(DamageType), nullable=False)
    description = Column(Text, nullable=False)  # Описание повреждения
    photos = Column(Text)  # JSON строка с путями к фото
    
    status = Column(Enum(DamageStatus), default=DamageStatus.PENDING)
    decision = Column(Text)  # Решение по отчету
    
    reported_by = Column(Integer, ForeignKey("users.id"), nullable=False)  # Кто сообщил
    checked_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Кто проверил
    
    reported_at = Column(DateTime(timezone=True), server_default=func.now())
    checked_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<DamageReport(id={self.id}, textbook_id={self.textbook_id}, status='{self.status}')>"