from sqlalchemy import Column, Integer, String, Integer as SqlInteger, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base


class Textbook(Base):
    __tablename__ = "textbooks"
    
    id = Column(Integer, primary_key=True, index=True)
    qr_code = Column(String, unique=True, index=True, nullable=False)  # Уникальный QR код
    subject = Column(String, nullable=False)  # Предмет
    title = Column(String, nullable=False)    # Название учебника
    author = Column(String)                   # Автор
    publisher = Column(String)                # Издательство
    year = Column(SqlInteger)                 # Год издания
    isbn = Column(String)                     # ISBN (если есть)
    inventory_number = Column(String)         # Инвентарный номер
    initial_condition = Column(Text)          # Начальное состояние
    current_condition = Column(Text)          # Текущее состояние
    is_active = Column(Boolean, default=True) # Активен ли учебник
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Textbook(id={self.id}, subject='{self.subject}', title='{self.title}')>"