from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    middle_name = Column(String)
    grade = Column(String, nullable=False)  # "7А"
    phone = Column(String)
    parent_phone = Column(String)
    max_user_id = Column(String)  # ID пользователя в МАКС
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    @property
    def full_name(self) -> str:
        """Полное имя ученика"""
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return " ".join(parts)
    
    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.full_name}', grade='{self.grade}')>"