from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import os
import uuid

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.textbook import Textbook
from app.models.damage_report import DamageReport, DamageType, DamageStatus
from app.schemas.damage_report import DamageReportCreate, DamageReportUpdate, DamageReportResponse
from app.api.auth import get_current_teacher
from app.services.image_storage import ImageStorage
from app.services.parent_notifications import ParentNotificationService

router = APIRouter()


async def save_damage_photos(files: List[UploadFile]) -> List[str]:
    """Сохраняет фото повреждений и возвращает пути к файлам"""
    if not files:
        return []
    
    image_storage = ImageStorage()
    photo_paths = []
    
    for file in files:
        if file.content_type and file.content_type.startswith('image/'):
            # Генерируем уникальное имя файла
            file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
            filename = f"damage_{uuid.uuid4().hex}{file_extension}"
            
            # Сохраняем файл
            file_path = await image_storage.save_image(file, filename)
            photo_paths.append(file_path)
    
    return photo_paths


@router.post("/", response_model=DamageReportResponse)
async def create_damage_report(
    textbook_id: int = Form(...),
    damage_type: DamageType = Form(...),
    description: str = Form(..., min_length=10, max_length=1000),
    photos: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Создание отчета о повреждении учебника"""
    # Проверяем существование учебника
    textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    # Сохраняем фото
    photo_paths = await save_damage_photos(photos)
    
    # Создаем отчет о повреждении
    damage_report = DamageReport(
        textbook_id=textbook_id,
        reported_by=current_user.id,
        damage_type=damage_type,
        description=description,
        photos=photo_paths,
        status=DamageStatus.PENDING,
        reported_at=datetime.utcnow()
    )
    
    db.add(damage_report)
    db.commit()
    db.refresh(damage_report)
    
    # Уведомляем родителей об утере
    if damage_type == DamageType.LOST:
        notification_service = ParentNotificationService()
        await notification_service.notify_lost_textbook(current_user.student_id, textbook_id, db)
    
    return damage_report


@router.get("/", response_model=List[DamageReportResponse])
async def get_damage_reports(
    skip: int = 0,
    limit: int = 100,
    textbook_id: Optional[int] = None,
    damage_type: Optional[DamageType] = None,
    status: Optional[DamageStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение списка отчетов о повреждениях с фильтрацией"""
    query = db.query(DamageReport)
    
    if textbook_id:
        query = query.filter(DamageReport.textbook_id == textbook_id)
    
    if damage_type:
        query = query.filter(DamageReport.damage_type == damage_type)
    
    if status:
        query = query.filter(DamageReport.status == status)
    
    damage_reports = query.offset(skip).limit(limit).all()
    return damage_reports


@router.get("/{damage_report_id}", response_model=DamageReportResponse)
async def get_damage_report(
    damage_report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение конкретного отчета о повреждении"""
    damage_report = db.query(DamageReport).filter(DamageReport.id == damage_report_id).first()
    if not damage_report:
        raise HTTPException(status_code=404, detail="Damage report not found")
    return damage_report


@router.put("/{damage_report_id}", response_model=DamageReportResponse)
async def update_damage_report(
    damage_report_id: int,
    damage_report_update: DamageReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Обновление отчета о повреждении"""
    db_damage_report = db.query(DamageReport).filter(DamageReport.id == damage_report_id).first()
    if not db_damage_report:
        raise HTTPException(status_code=404, detail="Damage report not found")
    
    # Обновляем только переданные поля
    update_data = damage_report_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_damage_report, field, value)
    
    # Если статус изменен на "проверен", устанавливаем время проверки
    if db_damage_report.status == DamageStatus.CHECKED:
        db_damage_report.checked_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_damage_report)
    return db_damage_report


@router.get("/textbook/{textbook_id}/history", response_model=List[DamageReportResponse])
async def get_textbook_damage_history(
    textbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение истории повреждений конкретного учебника"""
    damage_reports = db.query(DamageReport).filter(
        DamageReport.textbook_id == textbook_id
    ).order_by(DamageReport.reported_at.desc()).all()
    return damage_reports


@router.get("/pending-check", response_model=List[DamageReportResponse])
async def get_pending_damage_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение отчетов о повреждениях, ожидающих проверки"""
    # Находим отчеты, которые были созданы более 7 дней назад и еще не проверены
    check_deadline = datetime.utcnow() - timedelta(days=settings.DAMAGE_CHECK_DAYS)
    
    pending_reports = db.query(DamageReport).filter(
        DamageReport.status == DamageStatus.PENDING,
        DamageReport.reported_at <= check_deadline
    ).all()
    
    return pending_reports


@router.post("/{damage_report_id}/check", response_model=DamageReportResponse)
async def check_damage_report(
    damage_report_id: int,
    decision: str = Form(..., min_length=1, max_length=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Проверка отчета о повреждении"""
    damage_report = db.query(DamageReport).filter(DamageReport.id == damage_report_id).first()
    if not damage_report:
        raise HTTPException(status_code=404, detail="Damage report not found")
    
    if damage_report.status != DamageStatus.PENDING:
        raise HTTPException(status_code=400, detail="Damage report is already checked")
    
    # Обновляем статус и добавляем решение
    damage_report.status = DamageStatus.CHECKED
    damage_report.decision = decision
    damage_report.checked_by = current_user.id
    damage_report.checked_at = datetime.utcnow()
    
    db.commit()
    db.refresh(damage_report)
    
    return damage_report


@router.get("/statistics/summary")
async def get_damage_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение статистики по повреждениям"""
    total_reports = db.query(DamageReport).count()
    pending_reports = db.query(DamageReport).filter(DamageReport.status == DamageStatus.PENDING).count()
    checked_reports = db.query(DamageReport).filter(DamageReport.status == DamageStatus.CHECKED).count()
    
    # Статистика по типам повреждений
    damage_type_stats = db.query(DamageReport.damage_type, db.func.count(DamageReport.id)).group_by(DamageReport.damage_type).all()
    
    return {
        "total_reports": total_reports,
        "pending_reports": pending_reports,
        "checked_reports": checked_reports,
        "damage_type_statistics": dict(damage_type_stats)
    } 