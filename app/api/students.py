from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.user import User
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse, StudentList
from app.api.auth import get_current_teacher

router = APIRouter()


@router.post("/", response_model=StudentResponse)
async def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Создание нового ученика"""
    # Проверяем, что ученик с таким именем и классом не существует
    existing_student = db.query(Student).filter(
        Student.first_name == student.first_name,
        Student.last_name == student.last_name,
        Student.grade == student.grade
    ).first()
    
    if existing_student:
        raise HTTPException(status_code=400, detail="Student already exists")
    
    db_student = Student(
        first_name=student.first_name,
        last_name=student.last_name,
        middle_name=student.middle_name,
        grade=student.grade,
        phone=student.phone,
        parent_phone=student.parent_phone,
        max_user_id=student.max_user_id
    )
    
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    return db_student


@router.get("/", response_model=List[StudentList])
async def get_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    grade: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение списка учеников с фильтрацией"""
    query = db.query(Student)
    
    if grade:
        query = query.filter(Student.grade == grade)
    
    if is_active is not None:
        query = query.filter(Student.is_active == is_active)
    
    students = query.offset(skip).limit(limit).all()
    return students


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение конкретного ученика"""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    student_update: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Обновление данных ученика"""
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Обновляем только переданные поля
    update_data = student_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_student, field, value)
    
    db.commit()
    db.refresh(db_student)
    return db_student


@router.delete("/{student_id}")
async def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Удаление ученика (мягкое удаление - деактивация)"""
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Мягкое удаление - деактивируем ученика
    db_student.is_active = False
    db.commit()
    
    return {"message": "Student deactivated successfully"}


@router.get("/grade/{grade}", response_model=List[StudentList])
async def get_students_by_grade(
    grade: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Получение всех учеников конкретного класса"""
    students = db.query(Student).filter(
        Student.grade == grade,
        Student.is_active == True
    ).all()
    return students


@router.post("/bulk", response_model=List[StudentResponse])
async def create_students_bulk(
    students: List[StudentCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Массовое создание учеников"""
    created_students = []
    
    for student_data in students:
        # Проверяем, что ученик не существует
        existing_student = db.query(Student).filter(
            Student.first_name == student_data.first_name,
            Student.last_name == student_data.last_name,
            Student.grade == student_data.grade
        ).first()
        
        if existing_student:
            continue  # Пропускаем существующих учеников
        
        db_student = Student(
            first_name=student_data.first_name,
            last_name=student_data.last_name,
            middle_name=student_data.middle_name,
            grade=student_data.grade,
            phone=student_data.phone,
            parent_phone=student_data.parent_phone,
            max_user_id=student_data.max_user_id
        )
        
        db.add(db_student)
        created_students.append(db_student)
    
    db.commit()
    
    # Обновляем объекты после коммита
    for student in created_students:
        db.refresh(student)
    
    return created_students 