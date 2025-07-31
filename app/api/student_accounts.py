from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.student import Student
from app.schemas.user import UserCreate, UserResponse
from app.schemas.student import StudentResponse
from app.api.auth import get_current_teacher, get_password_hash
from app.services.max_bot_client import MaxBotClient

router = APIRouter()


@router.post("/create", response_model=UserResponse)
async def create_student_account(
    student_id: int,
    username: str,
    password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Создание аккаунта для ученика"""
    # Проверяем существование ученика
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    if not student.is_active:
        raise HTTPException(status_code=400, detail="Student is not active")
    
    # Проверяем, что у ученика еще нет аккаунта
    existing_user = db.query(User).filter(User.student_id == student_id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Student already has an account")
    
    # Проверяем, что username не занят
    existing_username = db.query(User).filter(User.username == username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Создаем аккаунт ученика
    hashed_password = get_password_hash(password)
    student_user = User(
        username=username,
        password_hash=hashed_password,
        role=UserRole.STUDENT,
        student_id=student_id,
        is_active=True
    )
    
    db.add(student_user)
    db.commit()
    db.refresh(student_user)
    
    return student_user


@router.post("/link-max", response_model=UserResponse)
async def link_student_to_max(
    user_id: int,
    max_user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Связывание аккаунта ученика с МАКС"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=400, detail="Can only link student accounts")
    
    # Обновляем max_user_id у ученика
    student = db.query(Student).filter(Student.id == user.student_id).first()
    if student:
        student.max_user_id = max_user_id
        db.commit()
        db.refresh(user)
    
    return user


@router.get("/students", response_model=List[dict])
async def get_students_with_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение списка учеников с информацией об аккаунтах"""
    students = db.query(Student).filter(Student.is_active == True).all()
    
    result = []
    for student in students:
        user = db.query(User).filter(User.student_id == student.id).first()
        result.append({
            "student_id": student.id,
            "full_name": student.full_name,
            "grade": student.grade,
            "phone": student.phone,
            "parent_phone": student.parent_phone,
            "has_account": user is not None,
            "username": user.username if user else None,
            "max_user_id": student.max_user_id,
            "account_active": user.is_active if user else False
        })
    
    return result


@router.post("/bulk-create", response_model=List[UserResponse])
async def bulk_create_student_accounts(
    accounts_data: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Массовое создание аккаунтов для учеников"""
    created_accounts = []
    
    for account_data in accounts_data:
        student_id = account_data.get("student_id")
        username = account_data.get("username")
        password = account_data.get("password")
        
        if not all([student_id, username, password]):
            continue
        
        # Проверяем существование ученика
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student or not student.is_active:
            continue
        
        # Проверяем, что у ученика еще нет аккаунта
        existing_user = db.query(User).filter(User.student_id == student_id).first()
        if existing_user:
            continue
        
        # Проверяем, что username не занят
        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            continue
        
        # Создаем аккаунт ученика
        hashed_password = get_password_hash(password)
        student_user = User(
            username=username,
            password_hash=hashed_password,
            role=UserRole.STUDENT,
            student_id=student_id,
            is_active=True
        )
        
        db.add(student_user)
        created_accounts.append(student_user)
    
    db.commit()
    
    # Обновляем объекты после коммита
    for account in created_accounts:
        db.refresh(account)
    
    return created_accounts


@router.post("/{user_id}/activate")
async def activate_student_account(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Активация аккаунта ученика"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=400, detail="Can only activate student accounts")
    
    user.is_active = True
    db.commit()
    
    return {"message": "Student account activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_student_account(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Деактивация аккаунта ученика"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=400, detail="Can only deactivate student accounts")
    
    user.is_active = False
    db.commit()
    
    return {"message": "Student account deactivated successfully"} 