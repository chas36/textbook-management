from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class DamageReport(Base):
    __tablename__ = "damage_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    textbook_id = Column(Integer, ForeignKey("textbooks.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Кто сообщил
    
    description = Column(Text, nullable=False)  # Описание повреждения
    photo_paths = Column(Text)  # JSON строка с путями к фото
    
    reported_by = Column(String, nullable=False)  # "student" или "teacher"
    is_during_check_period = Column(Boolean, default=False)  # Был ли добавлен в первые 7 дней
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    textbook = relationship("Textbook", back_populates="damage_reports")
    student = relationship("Student", back_populates="damage_reports")
    user = relationship("User", back_populates="damage_reports")
    
    def __repr__(self):
        return f"<DamageReport(id={self.id}, textbook_id={self.textbook_id})>"


# Добавим обратные связи
from app.models.textbook import Textbook
from app.models.student import Student
from app.models.user import User

Textbook.damage_reports = relationship("DamageReport", back_populates="textbook")
Student.damage_reports = relationship("DamageReport", back_populates="student")
User.damage_reports = relationship("DamageReport", back_populates="user")