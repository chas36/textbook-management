from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    class_number = Column(String, nullable=False)  # "7А"
    phone = Column(String)
    parent_phone = Column(String)
    max_user_id = Column(String)  # ID пользователя в МАКС
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Student(id={self.id}, name='{self.full_name}', class='{self.class_number}')>"