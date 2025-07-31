from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.student import Student
from app.models.textbook import Textbook
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.schemas.transaction import (
    TransactionResponse, TransactionList, BulkIssueRequest, BulkReturnRequest
)
from app.api.auth import get_current_teacher
from app.services.image_storage import ImageStorage
from app.services.parent_notifications import ParentNotificationService

router = APIRouter()


async def save_transaction_photos(files: List[UploadFile]) -> List[str]:
    """Сохраняет фото транзакции и возвращает пути к файлам"""
    if not files:
        return []
    
    image_storage = ImageStorage()
    photo_paths = []
    
    for file in files:
        if file.content_type and file.content_type.startswith('image/'):
            # Генерируем уникальное имя файла
            file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
            filename = f"transaction_{uuid.uuid4().hex}{file_extension}"
            
            # Сохраняем файл
            file_path = await image_storage.save_image(file, filename)
            photo_paths.append(file_path)
    
    return photo_paths


@router.post("/issue", response_model=TransactionResponse)
async def issue_textbook(
    textbook_id: int = Form(...),
    student_id: int = Form(...),
    notes: Optional[str] = Form(None),
    photos: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Выдача учебника ученику"""
    # Проверяем существование учебника
    textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    if not textbook.is_active:
        raise HTTPException(status_code=400, detail="Textbook is not active")
    
    # Проверяем существование ученика
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if not student.is_active:
        raise HTTPException(status_code=400, detail="Student is not active")
    
    # Проверяем, не выдан ли уже учебник
    active_transaction = db.query(Transaction).filter(
        Transaction.textbook_id == textbook_id,
        Transaction.transaction_type == TransactionType.ISSUE,
        Transaction.status == TransactionStatus.COMPLETED
    ).first()
    
    if active_transaction:
        raise HTTPException(status_code=400, detail="Textbook is already issued")
    
    # Сохраняем фото
    photo_paths = await save_transaction_photos(photos)
    
    # Создаем транзакцию выдачи
    transaction = Transaction(
        textbook_id=textbook_id,
        student_id=student_id,
        transaction_type=TransactionType.ISSUE,
        status=TransactionStatus.COMPLETED,
        notes=notes,
        photos=photo_paths,
        issued_by=current_user.id,
        issued_at=datetime.utcnow()
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # Уведомляем родителей
    notification_service = ParentNotificationService()
    await notification_service.notify_issue_textbooks(student_id, [textbook_id], db)
    
    return transaction


@router.post("/return", response_model=TransactionResponse)
async def return_textbook(
    textbook_id: int = Form(...),
    notes: Optional[str] = Form(None),
    photos: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Возврат учебника"""
    # Проверяем существование учебника
    textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    # Находим активную транзакцию выдачи
    issue_transaction = db.query(Transaction).filter(
        Transaction.textbook_id == textbook_id,
        Transaction.transaction_type == TransactionType.ISSUE,
        Transaction.status == TransactionStatus.COMPLETED
    ).first()
    
    if not issue_transaction:
        raise HTTPException(status_code=400, detail="Textbook is not issued")
    
    # Сохраняем фото
    photo_paths = await save_transaction_photos(photos)
    
    # Создаем транзакцию возврата
    return_transaction = Transaction(
        textbook_id=textbook_id,
        student_id=issue_transaction.student_id,
        transaction_type=TransactionType.RETURN,
        status=TransactionStatus.COMPLETED,
        notes=notes,
        photos=photo_paths,
        issued_by=current_user.id,
        issued_at=datetime.utcnow(),
        returned_at=datetime.utcnow()
    )
    
    db.add(return_transaction)
    db.commit()
    db.refresh(return_transaction)
    
    # Уведомляем родителей
    notification_service = ParentNotificationService()
    await notification_service.notify_return_textbooks(issue_transaction.student_id, [textbook_id], db)
    
    return return_transaction


@router.post("/bulk-issue", response_model=List[TransactionResponse])
async def bulk_issue_textbooks(
    request: BulkIssueRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Массовая выдача учебников"""
    # Проверяем существование ученика
    student = db.query(Student).filter(Student.id == request.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if not student.is_active:
        raise HTTPException(status_code=400, detail="Student is not active")
    
    transactions = []
    
    for textbook_id in request.textbook_ids:
        # Проверяем существование учебника
        textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
        if not textbook or not textbook.is_active:
            continue
        
        # Проверяем, не выдан ли уже учебник
        active_transaction = db.query(Transaction).filter(
            Transaction.textbook_id == textbook_id,
            Transaction.transaction_type == TransactionType.ISSUE,
            Transaction.status == TransactionStatus.COMPLETED
        ).first()
        
        if active_transaction:
            continue
        
        # Создаем транзакцию выдачи
        transaction = Transaction(
            textbook_id=textbook_id,
            student_id=request.student_id,
            transaction_type=TransactionType.ISSUE,
            status=TransactionStatus.COMPLETED,
            notes=request.notes,
            issued_by=current_user.id,
            issued_at=datetime.utcnow()
        )
        
        db.add(transaction)
        transactions.append(transaction)
    
    db.commit()
    
    # Обновляем объекты после коммита
    for transaction in transactions:
        db.refresh(transaction)
    
    return transactions


@router.post("/bulk-return", response_model=List[TransactionResponse])
async def bulk_return_textbooks(
    request: BulkReturnRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Массовый возврат учебников"""
    transactions = []
    
    for textbook_id in request.textbook_ids:
        # Проверяем существование учебника
        textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
        if not textbook:
            continue
        
        # Находим активную транзакцию выдачи
        issue_transaction = db.query(Transaction).filter(
            Transaction.textbook_id == textbook_id,
            Transaction.transaction_type == TransactionType.ISSUE,
            Transaction.status == TransactionStatus.COMPLETED
        ).first()
        
        if not issue_transaction:
            continue
        
        # Создаем транзакцию возврата
        return_transaction = Transaction(
            textbook_id=textbook_id,
            student_id=issue_transaction.student_id,
            transaction_type=TransactionType.RETURN,
            status=TransactionStatus.COMPLETED,
            notes=request.notes,
            issued_by=current_user.id,
            issued_at=datetime.utcnow(),
            returned_at=datetime.utcnow()
        )
        
        db.add(return_transaction)
        transactions.append(return_transaction)
    
    db.commit()
    
    # Обновляем объекты после коммита
    for transaction in transactions:
        db.refresh(transaction)
    
    return transactions


@router.get("/", response_model=List[TransactionList])
async def get_transactions(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[int] = None,
    textbook_id: Optional[int] = None,
    transaction_type: Optional[TransactionType] = None,
    status: Optional[TransactionStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение списка транзакций с фильтрацией"""
    query = db.query(Transaction)
    
    if student_id:
        query = query.filter(Transaction.student_id == student_id)
    
    if textbook_id:
        query = query.filter(Transaction.textbook_id == textbook_id)
    
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    
    if status:
        query = query.filter(Transaction.status == status)
    
    transactions = query.offset(skip).limit(limit).all()
    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение конкретной транзакции"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.get("/student/{student_id}/active", response_model=List[TransactionResponse])
async def get_student_active_textbooks(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение активных учебников ученика (выданных, но не возвращенных)"""
    # Находим все выданные учебники ученика
    issued_transactions = db.query(Transaction).filter(
        Transaction.student_id == student_id,
        Transaction.transaction_type == TransactionType.ISSUE,
        Transaction.status == TransactionStatus.COMPLETED
    ).all()
    
    active_textbooks = []
    
    for issue_transaction in issued_transactions:
        # Проверяем, есть ли возврат для этого учебника
        return_transaction = db.query(Transaction).filter(
            Transaction.textbook_id == issue_transaction.textbook_id,
            Transaction.transaction_type == TransactionType.RETURN,
            Transaction.status == TransactionStatus.COMPLETED
        ).first()
        
        if not return_transaction:
            active_textbooks.append(issue_transaction)
    
    return active_textbooks 