from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import uuid

from app.core.database import get_db
from app.models.user import User
from app.models.textbook import Textbook
from app.models.found_report import FoundReport, FoundStatus
from app.schemas.found_report import FoundReportCreate, FoundReportUpdate, FoundReportResponse
from app.api.auth import get_current_teacher
from app.services.image_storage import ImageStorage
from app.services.parent_notifications import ParentNotificationService

router = APIRouter()


async def save_found_photos(files: List[UploadFile]) -> List[str]:
    """Сохраняет фото найденного учебника и возвращает пути к файлам"""
    if not files:
        return []
    
    image_storage = ImageStorage()
    photo_paths = []
    
    for file in files:
        if file.content_type and file.content_type.startswith('image/'):
            # Генерируем уникальное имя файла
            file_extension = os.path.splitext(file.filename)[1] if file.filename else '.jpg'
            filename = f"found_{uuid.uuid4().hex}{file_extension}"
            
            # Сохраняем файл
            file_path = await image_storage.save_image(file, filename)
            photo_paths.append(file_path)
    
    return photo_paths


@router.post("/", response_model=FoundReportResponse)
async def create_found_report(
    textbook_id: int = Form(...),
    found_location: str = Form(..., min_length=5, max_length=200),
    description: Optional[str] = Form(None, max_length=500),
    photos: List[UploadFile] = File([]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Создание отчета о найденном учебнике"""
    # Проверяем существование учебника
    textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    # Сохраняем фото
    photo_paths = await save_found_photos(photos)
    
    # Создаем отчет о находке
    found_report = FoundReport(
        textbook_id=textbook_id,
        reported_by=current_user.id,
        found_location=found_location,
        description=description,
        photos=photo_paths,
        status=FoundStatus.FOUND,
        found_at=datetime.utcnow()
    )
    
    db.add(found_report)
    db.commit()
    db.refresh(found_report)
    
    # Уведомляем родителей владельца
    notification_service = ParentNotificationService()
    await notification_service.notify_found_textbook(current_user.student_id, textbook_id, db)
    
    return found_report


@router.get("/", response_model=List[FoundReportResponse])
async def get_found_reports(
    skip: int = 0,
    limit: int = 100,
    textbook_id: Optional[int] = None,
    status: Optional[FoundStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение списка отчетов о находках с фильтрацией"""
    query = db.query(FoundReport)
    
    if textbook_id:
        query = query.filter(FoundReport.textbook_id == textbook_id)
    
    if status:
        query = query.filter(FoundReport.status == status)
    
    found_reports = query.offset(skip).limit(limit).all()
    return found_reports


@router.get("/{found_report_id}", response_model=FoundReportResponse)
async def get_found_report(
    found_report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение конкретного отчета о находке"""
    found_report = db.query(FoundReport).filter(FoundReport.id == found_report_id).first()
    if not found_report:
        raise HTTPException(status_code=404, detail="Found report not found")
    return found_report


@router.put("/{found_report_id}", response_model=FoundReportResponse)
async def update_found_report(
    found_report_id: int,
    found_report_update: FoundReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Обновление отчета о находке"""
    db_found_report = db.query(FoundReport).filter(FoundReport.id == found_report_id).first()
    if not db_found_report:
        raise HTTPException(status_code=404, detail="Found report not found")
    
    # Обновляем только переданные поля
    update_data = found_report_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_found_report, field, value)
    
    # Если статус изменен на "возвращен", устанавливаем время возврата
    if db_found_report.status == FoundStatus.RETURNED:
        db_found_report.returned_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_found_report)
    return db_found_report


@router.post("/{found_report_id}/return", response_model=FoundReportResponse)
async def mark_as_returned(
    found_report_id: int,
    notes: Optional[str] = Form(None, max_length=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Отметить найденный учебник как возвращенный"""
    found_report = db.query(FoundReport).filter(FoundReport.id == found_report_id).first()
    if not found_report:
        raise HTTPException(status_code=404, detail="Found report not found")
    
    if found_report.status == FoundStatus.RETURNED:
        raise HTTPException(status_code=400, detail="Textbook is already marked as returned")
    
    # Обновляем статус
    found_report.status = FoundStatus.RETURNED
    found_report.returned_at = datetime.utcnow()
    found_report.returned_by = current_user.id
    if notes:
        found_report.notes = notes
    
    db.commit()
    db.refresh(found_report)
    
    return found_report


@router.get("/textbook/{textbook_id}/history", response_model=List[FoundReportResponse])
async def get_textbook_found_history(
    textbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение истории находок конкретного учебника"""
    found_reports = db.query(FoundReport).filter(
        FoundReport.textbook_id == textbook_id
    ).order_by(FoundReport.found_at.desc()).all()
    return found_reports


@router.get("/active", response_model=List[FoundReportResponse])
async def get_active_found_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение активных отчетов о находках (найдены, но не возвращены)"""
    active_reports = db.query(FoundReport).filter(
        FoundReport.status == FoundStatus.FOUND
    ).all()
    return active_reports


@router.get("/statistics/summary")
async def get_found_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение статистики по находкам"""
    total_reports = db.query(FoundReport).count()
    found_reports = db.query(FoundReport).filter(FoundReport.status == FoundStatus.FOUND).count()
    returned_reports = db.query(FoundReport).filter(FoundReport.status == FoundStatus.RETURNED).count()
    
    return {
        "total_reports": total_reports,
        "found_reports": found_reports,
        "returned_reports": returned_reports,
        "return_rate": (returned_reports / total_reports * 100) if total_reports > 0 else 0
    } 