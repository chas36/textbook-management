from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.textbook import Textbook
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.damage_report import DamageReport, DamageType, DamageStatus
from app.models.found_report import FoundReport, FoundStatus
from app.schemas.transaction import TransactionResponse
from app.api.auth import get_current_active_user
from app.services.image_storage import ImageStorage
from app.services.max_bot_client import MaxBotClient

router = APIRouter()


async def get_current_student(current_user: User = Depends(get_current_active_user)) -> User:
    """Получение текущего ученика"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=403,
            detail="Only students can access this endpoint"
        )
    return current_user


@router.get("/my-textbooks", response_model=List[dict])
async def get_my_textbooks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Получение списка учебников ученика"""
    # Получаем активные учебники ученика (выданные, но не возвращенные)
    issued_transactions = db.query(Transaction).filter(
        Transaction.student_id == current_user.student_id,
        Transaction.transaction_type == TransactionType.ISSUE,
        Transaction.status == TransactionStatus.COMPLETED
    ).all()
    
    my_textbooks = []
    
    for issue_transaction in issued_transactions:
        # Проверяем, есть ли возврат для этого учебника
        return_transaction = db.query(Transaction).filter(
            Transaction.textbook_id == issue_transaction.textbook_id,
            Transaction.transaction_type == TransactionType.RETURN,
            Transaction.status == TransactionStatus.COMPLETED
        ).first()
        
        if not return_transaction:
            # Учебник еще не возвращен
            textbook = db.query(Textbook).filter(Textbook.id == issue_transaction.textbook_id).first()
            if textbook:
                my_textbooks.append({
                    "textbook_id": textbook.id,
                    "qr_code": textbook.qr_code,
                    "subject": textbook.subject,
                    "title": textbook.title,
                    "author": textbook.author,
                    "issued_at": issue_transaction.issued_at,
                    "photos": json.loads(issue_transaction.photos) if issue_transaction.photos else []
                })
    
    return my_textbooks


@router.get("/textbook/{qr_code}/info")
async def get_textbook_info_by_qr(
    qr_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Получение информации об учебнике по QR коду"""
    textbook = db.query(Textbook).filter(Textbook.qr_code == qr_code).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    # Проверяем, кому выдан учебник
    active_transaction = db.query(Transaction).filter(
        Transaction.textbook_id == textbook.id,
        Transaction.transaction_type == TransactionType.ISSUE,
        Transaction.status == TransactionStatus.COMPLETED
    ).first()
    
    if not active_transaction:
        return {
            "textbook_id": textbook.id,
            "qr_code": textbook.qr_code,
            "subject": textbook.subject,
            "title": textbook.title,
            "author": textbook.author,
            "status": "available",
            "issued_to": None
        }
    
    # Проверяем, есть ли возврат
    return_transaction = db.query(Transaction).filter(
        Transaction.textbook_id == textbook.id,
        Transaction.transaction_type == TransactionType.RETURN,
        Transaction.status == TransactionStatus.COMPLETED
    ).first()
    
    if return_transaction:
        return {
            "textbook_id": textbook.id,
            "qr_code": textbook.qr_code,
            "subject": textbook.subject,
            "title": textbook.title,
            "author": textbook.author,
            "status": "available",
            "issued_to": None
        }
    
    # Учебник выдан
    student = db.query(Student).filter(Student.id == active_transaction.student_id).first()
    is_mine = active_transaction.student_id == current_user.student_id
    
    return {
        "textbook_id": textbook.id,
        "qr_code": textbook.qr_code,
        "subject": textbook.subject,
        "title": textbook.title,
        "author": textbook.author,
        "status": "issued",
        "issued_to": student.full_name if student else "Unknown",
        "is_mine": is_mine,
        "issued_at": active_transaction.issued_at
    }


@router.post("/report-damage")
async def report_damage(
    textbook_id: int = Form(...),
    damage_type: DamageType = Form(...),
    description: str = Form(..., min_length=10, max_length=1000),
    photos: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Сообщение о повреждении учебника"""
    # Проверяем, что учебник выдан этому ученику
    active_transaction = db.query(Transaction).filter(
        Transaction.textbook_id == textbook_id,
        Transaction.student_id == current_user.student_id,
        Transaction.transaction_type == TransactionType.ISSUE,
        Transaction.status == TransactionStatus.COMPLETED
    ).first()
    
    if not active_transaction:
        raise HTTPException(status_code=400, detail="Textbook is not issued to you")
    
    # Проверяем, что учебник не возвращен
    return_transaction = db.query(Transaction).filter(
        Transaction.textbook_id == textbook_id,
        Transaction.transaction_type == TransactionType.RETURN,
        Transaction.status == TransactionStatus.COMPLETED
    ).first()
    
    if return_transaction:
        raise HTTPException(status_code=400, detail="Textbook is already returned")
    
    # Сохраняем фото
    image_storage = ImageStorage()
    photo_paths = []
    
    for file in photos:
        if file.content_type and file.content_type.startswith('image/'):
            import os
            import uuid
            file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
            filename = f"damage_{uuid.uuid4().hex}{file_extension}"
            file_path = await image_storage.save_image(file, filename)
            photo_paths.append(file_path)
    
    # Определяем, в течение ли первой недели после выдачи
    week_after_issue = active_transaction.issued_at + timedelta(days=7)
    is_during_check_period = datetime.utcnow() <= week_after_issue
    
    # Создаем отчет о повреждении
    damage_report = DamageReport(
        textbook_id=textbook_id,
        reported_by=current_user.id,
        damage_type=damage_type,
        description=description,
        photos=json.dumps(photo_paths),
        status=DamageStatus.PENDING,
        reported_at=datetime.utcnow()
    )
    
    db.add(damage_report)
    db.commit()
    db.refresh(damage_report)
    
    # Уведомляем учителя через МАКС
    max_bot = MaxBotClient()
    await max_bot.send_damage_notification(
        student_name=current_user.username,
        textbook_title=active_transaction.textbook.title,
        damage_type=damage_type.value,
        is_during_check_period=is_during_check_period
    )
    
    return {
        "message": "Damage reported successfully",
        "damage_report_id": damage_report.id,
        "is_during_check_period": is_during_check_period
    }


@router.post("/report-lost")
async def report_lost_textbook(
    textbook_id: int = Form(...),
    description: str = Form(..., min_length=10, max_length=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Сообщение об утере учебника"""
    # Проверяем, что учебник выдан этому ученику
    active_transaction = db.query(Transaction).filter(
        Transaction.textbook_id == textbook_id,
        Transaction.student_id == current_user.student_id,
        Transaction.transaction_type == TransactionType.ISSUE,
        Transaction.status == TransactionStatus.COMPLETED
    ).first()
    
    if not active_transaction:
        raise HTTPException(status_code=400, detail="Textbook is not issued to you")
    
    # Проверяем, что учебник не возвращен
    return_transaction = db.query(Transaction).filter(
        Transaction.textbook_id == textbook_id,
        Transaction.transaction_type == TransactionType.RETURN,
        Transaction.status == TransactionStatus.COMPLETED
    ).first()
    
    if return_transaction:
        raise HTTPException(status_code=400, detail="Textbook is already returned")
    
    # Создаем отчет о повреждении типа "утерян"
    damage_report = DamageReport(
        textbook_id=textbook_id,
        reported_by=current_user.id,
        damage_type=DamageType.LOST,
        description=description,
        photos="[]",
        status=DamageStatus.PENDING,
        reported_at=datetime.utcnow()
    )
    
    db.add(damage_report)
    db.commit()
    db.refresh(damage_report)
    
    # Уведомляем учителя и родителей через МАКС
    max_bot = MaxBotClient()
    student = db.query(Student).filter(Student.id == current_user.student_id).first()
    
    await max_bot.send_lost_notification(
        student_name=student.full_name,
        textbook_title=active_transaction.textbook.title,
        parent_phone=student.parent_phone
    )
    
    return {
        "message": "Lost textbook reported successfully",
        "damage_report_id": damage_report.id
    }


@router.post("/report-found")
async def report_found_textbook(
    qr_code: str = Form(...),
    found_location: str = Form(..., min_length=5, max_length=200),
    description: Optional[str] = Form(None, max_length=500),
    photos: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Сообщение о найденном учебнике"""
    # Находим учебник по QR коду
    textbook = db.query(Textbook).filter(Textbook.qr_code == qr_code).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    # Сохраняем фото
    image_storage = ImageStorage()
    photo_paths = []
    
    for file in photos:
        if file.content_type and file.content_type.startswith('image/'):
            import os
            import uuid
            file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
            filename = f"found_{uuid.uuid4().hex}{file_extension}"
            file_path = await image_storage.save_image(file, filename)
            photo_paths.append(file_path)
    
    # Создаем отчет о находке
    found_report = FoundReport(
        textbook_id=textbook.id,
        reported_by=current_user.id,
        found_location=found_location,
        description=description,
        photos=json.dumps(photo_paths),
        status=FoundStatus.FOUND,
        found_at=datetime.utcnow()
    )
    
    db.add(found_report)
    db.commit()
    db.refresh(found_report)
    
    # Уведомляем учителя через МАКС
    max_bot = MaxBotClient()
    student = db.query(Student).filter(Student.id == current_user.student_id).first()
    
    await max_bot.send_found_notification(
        finder_name=student.full_name,
        textbook_title=textbook.title,
        found_location=found_location
    )
    
    return {
        "message": "Found textbook reported successfully",
        "found_report_id": found_report.id
    }


@router.get("/damage-reminder")
async def get_damage_reminder(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """Получение напоминания о необходимости проверить повреждения"""
    # Получаем учебники, выданные в течение последней недели
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    recent_transactions = db.query(Transaction).filter(
        Transaction.student_id == current_user.student_id,
        Transaction.transaction_type == TransactionType.ISSUE,
        Transaction.status == TransactionStatus.COMPLETED,
        Transaction.issued_at >= week_ago
    ).all()
    
    textbooks_to_check = []
    
    for transaction in recent_transactions:
        # Проверяем, есть ли уже отчеты о повреждениях
        damage_reports = db.query(DamageReport).filter(
            DamageReport.textbook_id == transaction.textbook_id,
            DamageReport.reported_by == current_user.id
        ).all()
        
        if not damage_reports:
            textbook = db.query(Textbook).filter(Textbook.id == transaction.textbook_id).first()
            if textbook:
                textbooks_to_check.append({
                    "textbook_id": textbook.id,
                    "subject": textbook.subject,
                    "title": textbook.title,
                    "issued_at": transaction.issued_at,
                    "deadline": transaction.issued_at + timedelta(days=7)
                })
    
    return {
        "textbooks_to_check": textbooks_to_check,
        "message": f"You need to check {len(textbooks_to_check)} textbooks for damage within the first week"
    } 