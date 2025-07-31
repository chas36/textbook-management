from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.student import Student
from app.models.textbook import Textbook
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.damage_report import DamageReport, DamageType, DamageStatus
from app.api.auth import get_current_teacher
from app.services.parent_notifications import ParentNotificationService

router = APIRouter()


@router.get("/issue-summary")
async def get_issue_summary(
    grade: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Отчет по выданным учебникам"""
    # Базовый запрос для активных транзакций выдачи
    query = db.query(Transaction).filter(
        Transaction.transaction_type == TransactionType.ISSUE,
        Transaction.status == TransactionStatus.COMPLETED
    )
    
    if grade:
        # Фильтруем по классу
        students_in_grade = db.query(Student.id).filter(Student.grade == grade).subquery()
        query = query.filter(Transaction.student_id.in_(students_in_grade))
    
    issued_transactions = query.all()
    
    # Группируем по ученикам
    students_summary = {}
    
    for transaction in issued_transactions:
        student = db.query(Student).filter(Student.id == transaction.student_id).first()
        textbook = db.query(Textbook).filter(Textbook.id == transaction.textbook_id).first()
        
        if not student or not textbook:
            continue
        
        # Проверяем, есть ли возврат
        return_transaction = db.query(Transaction).filter(
            Transaction.textbook_id == transaction.textbook_id,
            Transaction.transaction_type == TransactionType.RETURN,
            Transaction.status == TransactionStatus.COMPLETED
        ).first()
        
        if student.id not in students_summary:
            students_summary[student.id] = {
                "student_id": student.id,
                "full_name": student.full_name,
                "grade": student.grade,
                "phone": student.phone,
                "parent_phone": student.parent_phone,
                "issued_textbooks": [],
                "returned_textbooks": [],
                "not_returned_textbooks": []
            }
        
        textbook_info = {
            "textbook_id": textbook.id,
            "qr_code": textbook.qr_code,
            "subject": textbook.subject,
            "title": textbook.title,
            "issued_at": transaction.issued_at
        }
        
        if return_transaction:
            textbook_info["returned_at"] = return_transaction.issued_at
            students_summary[student.id]["returned_textbooks"].append(textbook_info)
        else:
            students_summary[student.id]["not_returned_textbooks"].append(textbook_info)
        
        students_summary[student.id]["issued_textbooks"].append(textbook_info)
    
    # Формируем итоговую статистику
    total_students = len(students_summary)
    total_issued = sum(len(data["issued_textbooks"]) for data in students_summary.values())
    total_returned = sum(len(data["returned_textbooks"]) for data in students_summary.values())
    total_not_returned = sum(len(data["not_returned_textbooks"]) for data in students_summary.values())
    
    return {
        "summary": {
            "total_students": total_students,
            "total_issued": total_issued,
            "total_returned": total_returned,
            "total_not_returned": total_not_returned
        },
        "students": list(students_summary.values())
    }


@router.get("/not-issued")
async def get_not_issued_report(
    grade: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Отчет по ученикам, которые не получили учебники"""
    # Получаем всех активных учеников
    students_query = db.query(Student).filter(Student.is_active == True)
    if grade:
        students_query = students_query.filter(Student.grade == grade)
    
    students = students_query.all()
    
    not_issued_students = []
    
    for student in students:
        # Проверяем, есть ли у ученика активные транзакции выдачи
        active_issues = db.query(Transaction).filter(
            Transaction.student_id == student.id,
            Transaction.transaction_type == TransactionType.ISSUE,
            Transaction.status == TransactionStatus.COMPLETED
        ).all()
        
        if not active_issues:
            not_issued_students.append({
                "student_id": student.id,
                "full_name": student.full_name,
                "grade": student.grade,
                "phone": student.phone,
                "parent_phone": student.parent_phone
            })
    
    return {
        "total_not_issued": len(not_issued_students),
        "students": not_issued_students
    }


@router.get("/not-returned")
async def get_not_returned_report(
    grade: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Отчет по ученикам, которые не сдали учебники"""
    # Получаем все активные транзакции выдачи
    issued_transactions = db.query(Transaction).filter(
        Transaction.transaction_type == TransactionType.ISSUE,
        Transaction.status == TransactionStatus.COMPLETED
    ).all()
    
    not_returned_students = {}
    
    for transaction in issued_transactions:
        student = db.query(Student).filter(Student.id == transaction.student_id).first()
        textbook = db.query(Textbook).filter(Textbook.id == transaction.textbook_id).first()
        
        if not student or not textbook:
            continue
        
        if grade and student.grade != grade:
            continue
        
        # Проверяем, есть ли возврат
        return_transaction = db.query(Transaction).filter(
            Transaction.textbook_id == transaction.textbook_id,
            Transaction.transaction_type == TransactionType.RETURN,
            Transaction.status == TransactionStatus.COMPLETED
        ).first()
        
        if not return_transaction:
            if student.id not in not_returned_students:
                not_returned_students[student.id] = {
                    "student_id": student.id,
                    "full_name": student.full_name,
                    "grade": student.grade,
                    "phone": student.phone,
                    "parent_phone": student.parent_phone,
                    "not_returned_textbooks": []
                }
            
            not_returned_students[student.id]["not_returned_textbooks"].append({
                "textbook_id": textbook.id,
                "qr_code": textbook.qr_code,
                "subject": textbook.subject,
                "title": textbook.title,
                "issued_at": transaction.issued_at
            })
    
    total_students = len(not_returned_students)
    total_textbooks = sum(len(data["not_returned_textbooks"]) for data in not_returned_students.values())
    
    return {
        "summary": {
            "total_students": total_students,
            "total_textbooks": total_textbooks
        },
        "students": list(not_returned_students.values())
    }


@router.get("/damage-summary")
async def get_damage_summary(
    grade: Optional[str] = None,
    damage_type: Optional[DamageType] = None,
    status: Optional[DamageStatus] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Отчет по повреждениям учебников"""
    query = db.query(DamageReport)
    
    if damage_type:
        query = query.filter(DamageReport.damage_type == damage_type)
    
    if status:
        query = query.filter(DamageReport.status == status)
    
    damage_reports = query.all()
    
    damage_summary = {}
    
    for report in damage_reports:
        textbook = db.query(Textbook).filter(Textbook.id == report.textbook_id).first()
        student = db.query(Student).filter(Student.id == report.reported_by).first()
        
        if not textbook or not student:
            continue
        
        if grade and student.grade != grade:
            continue
        
        if student.id not in damage_summary:
            damage_summary[student.id] = {
                "student_id": student.id,
                "full_name": student.full_name,
                "grade": student.grade,
                "damage_reports": []
            }
        
        damage_summary[student.id]["damage_reports"].append({
            "report_id": report.id,
            "textbook_id": textbook.id,
            "textbook_title": f"{textbook.subject}: {textbook.title}",
            "damage_type": report.damage_type.value,
            "description": report.description,
            "status": report.status.value,
            "reported_at": report.reported_at,
            "checked_at": report.checked_at
        })
    
    # Статистика по типам повреждений
    damage_type_stats = {}
    for report in damage_reports:
        damage_type = report.damage_type.value
        if damage_type not in damage_type_stats:
            damage_type_stats[damage_type] = 0
        damage_type_stats[damage_type] += 1
    
    total_reports = len(damage_reports)
    pending_reports = len([r for r in damage_reports if r.status == DamageStatus.PENDING])
    checked_reports = len([r for r in damage_reports if r.status == DamageStatus.CHECKED])
    
    return {
        "summary": {
            "total_reports": total_reports,
            "pending_reports": pending_reports,
            "checked_reports": checked_reports,
            "damage_type_statistics": damage_type_stats
        },
        "students": list(damage_summary.values())
    }


@router.post("/send-bulk-notifications")
async def send_bulk_notifications(
    notification_type: str,
    grade: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Отправка массовых уведомлений родителям"""
    notification_service = ParentNotificationService()
    
    if notification_type == "issue_summary":
        if not grade:
            raise HTTPException(status_code=400, detail="Grade is required for issue summary")
        await notification_service.notify_bulk_issue_summary(grade, db)
        return {"message": f"Bulk issue notifications sent for grade {grade}"}
    
    elif notification_type == "return_reminder":
        if not grade:
            raise HTTPException(status_code=400, detail="Grade is required for return reminder")
        await notification_service.notify_bulk_return_reminder(grade, db)
        return {"message": f"Bulk return reminders sent for grade {grade}"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid notification type")


@router.get("/textbook-history/{textbook_id}")
async def get_textbook_history(
    textbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """История конкретного учебника"""
    textbook = db.query(Textbook).filter(Textbook.id == textbook_id).first()
    if not textbook:
        raise HTTPException(status_code=404, detail="Textbook not found")
    
    # Получаем все транзакции
    transactions = db.query(Transaction).filter(
        Transaction.textbook_id == textbook_id
    ).order_by(Transaction.issued_at).all()
    
    # Получаем все отчеты о повреждениях
    damage_reports = db.query(DamageReport).filter(
        DamageReport.textbook_id == textbook_id
    ).order_by(DamageReport.reported_at).all()
    
    # Получаем все отчеты о находках
    found_reports = db.query(FoundReport).filter(
        FoundReport.textbook_id == textbook_id
    ).order_by(FoundReport.found_at).all()
    
    # Формируем историю
    history = []
    
    for transaction in transactions:
        student = db.query(Student).filter(Student.id == transaction.student_id).first()
        history.append({
            "date": transaction.issued_at,
            "type": "transaction",
            "action": transaction.transaction_type.value,
            "student_name": student.full_name if student else "Unknown",
            "status": transaction.status.value
        })
    
    for report in damage_reports:
        student = db.query(Student).filter(Student.id == report.reported_by).first()
        history.append({
            "date": report.reported_at,
            "type": "damage",
            "action": "damage_reported",
            "student_name": student.full_name if student else "Unknown",
            "damage_type": report.damage_type.value,
            "status": report.status.value
        })
    
    for report in found_reports:
        student = db.query(Student).filter(Student.id == report.reported_by).first()
        history.append({
            "date": report.found_at,
            "type": "found",
            "action": "found_reported",
            "student_name": student.full_name if student else "Unknown",
            "status": report.status.value
        })
    
    # Сортируем по дате
    history.sort(key=lambda x: x["date"])
    
    return {
        "textbook": {
            "id": textbook.id,
            "qr_code": textbook.qr_code,
            "subject": textbook.subject,
            "title": textbook.title,
            "author": textbook.author,
            "year": textbook.year
        },
        "history": history
    } 