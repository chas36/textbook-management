from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from app.core.database import get_db
from app.models.user import User
from app.models.textbook import Textbook
from app.schemas.textbook import (
    TextbookCreate, TextbookUpdate, TextbookResponse, 
    TextbookList, TextbookBulkCreate
)
from app.services.qr_generator import QRGenerator
from app.api.auth import get_current_teacher

router = APIRouter()


def generate_unique_qr_code() -> str:
    """Генерирует уникальный QR код для учебника"""
    return f"TEXTBOOK_{uuid.uuid4().hex[:12].upper()}"


@router.post("/", response_model=TextbookResponse)
async def create_textbook(
    textbook: TextbookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    # Генерируем уникальный QR код
    qr_code = generate_unique_qr_code()
    
    # Создаем учебник
    db_textbook = Textbook(
        qr_code=qr_code,
        subject=textbook.subject,
        title=textbook.title,
        author=textbook.author,
        publisher=textbook.publisher,
        year=textbook.year,
        isbn=textbook.isbn,
        inventory_number=textbook.inventory_number,
        initial_condition=textbook.initial_condition
    )
    
    db.add(db_textbook)
    db.commit()
    db.refresh(db_textbook)
    
    # Генерируем QR код изображение
    qr_generator = QRGenerator()
    qr_generator.generate_qr_code(db_textbook.qr_code, db_textbook.id)
    
    return db_textbook


@router.post("/bulk", response_model=List[TextbookResponse])
async def create_textbooks_bulk(
    request: TextbookBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Массовое создание учебников"""
    textbooks = []
    
    for i in range(request.quantity):
        # Генерируем уникальный QR код
        qr_code = generate_unique_qr_code()
        
        # Формируем инвентарный номер
        inventory_number = None
        if request.inventory_number_prefix:
            inventory_number = f"{request.inventory_number_prefix}{i+1:04d}"
        
        # Создаем учебник
        db_textbook = Textbook(
            qr_code=qr_code,
            subject=request.subject,
            title=request.title,
            author=request.author,
            publisher=request.publisher,
            year=request.year,
            isbn=request.isbn,
            inventory_number=inventory_number,
            initial_condition=request.initial_condition
        )
        
        db.add(db_textbook)
        textbooks.append(db_textbook)
    
    db.commit()
    
    # Генерируем QR коды для всех учебников
    qr_generator = QRGenerator()
    for textbook in textbooks:
        db.refresh(textbook)
        qr_generator.generate_qr_code(textbook.qr_code, textbook.id)
    
    return textbooks


@router.get("/", response_model=List[TextbookList])
async def get_textbooks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    subject: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение списка учебников с фильтрацией"""
    query = db.query(Textbook)
    
    if subject:
        query = query.filter(Textbook.subject.ilike(f"%{subject}%"))
    
    if is_active is not None:
        query = query.filter(Textbook.is_active == is_active)
    
    textbooks = query.offset(skip).limit(limit).all()
    return textbooks


@router.get("/{textbook_id}", response_model=TextbookResponse)
async def get_textbook(
    textbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение конкретного учебника"""
    textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    return textbook


@router.get("/qr/{qr_code}", response_model=TextbookResponse)
async def get_textbook_by_qr(
    qr_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение учебника по QR коду"""
    textbook = db.query(Textbook).filter(Textbook.qr_code == qr_code).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    return textbook


@router.put("/{textbook_id}", response_model=TextbookResponse)
async def update_textbook(
    textbook_id: int,
    textbook_update: TextbookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Обновление учебника"""
    db_textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not db_textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    # Обновляем только переданные поля
    update_data = textbook_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_textbook, field, value)
    
    db.commit()
    db.refresh(db_textbook)
    return db_textbook


@router.delete("/{textbook_id}")
async def delete_textbook(
    textbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Удаление учебника (мягкое удаление - деактивация)"""
    db_textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not db_textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    # Мягкое удаление - деактивируем учебник
    db_textbook.is_active = False
    db.commit()
    
    return {"message": "Textbook deactivated successfully"}


@router.get("/qr-code/{textbook_id}")
async def get_qr_code_image(
    textbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение изображения QR кода для учебника"""
    textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    # Генерируем QR код, если его нет
    qr_generator = QRGenerator()
    qr_path = qr_generator.generate_qr_code(textbook.qr_code, textbook.id)
    
    return {"qr_code_path": qr_path} 