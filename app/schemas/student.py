from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class StudentBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    grade: str = Field(..., pattern=r'^\d{1,2}[А-Я]$')  # Например: 5А, 10Б
    phone: Optional[str] = Field(None, pattern=r'^\+7\d{10}$')  # +7XXXXXXXXXX
    parent_phone: Optional[str] = Field(None, pattern=r'^\+7\d{10}$')
    max_user_id: Optional[str] = None  # ID пользователя в МАКС


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    middle_name: Optional[str] = Field(None, max_length=50)
    grade: Optional[str] = Field(None, pattern=r'^\d{1,2}[А-Я]$')
    phone: Optional[str] = Field(None, pattern=r'^\+7\d{10}$')
    parent_phone: Optional[str] = Field(None, pattern=r'^\+7\d{10}$')
    max_user_id: Optional[str] = None
    is_active: Optional[bool] = None


class StudentResponse(StudentBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StudentList(BaseModel):
    id: int
    full_name: str
    grade: str
    phone: Optional[str] = None
    parent_phone: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True 