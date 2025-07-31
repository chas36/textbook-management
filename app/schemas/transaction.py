from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TransactionType(str, Enum):
    ISSUE = "issue"
    RETURN = "return"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TransactionBase(BaseModel):
    textbook_id: int
    student_id: int
    transaction_type: TransactionType
    notes: Optional[str] = Field(None, max_length=500)


class TransactionCreate(TransactionBase):
    photos: Optional[List[str]] = None  # Пути к загруженным фото


class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    notes: Optional[str] = Field(None, max_length=500)
    photos: Optional[List[str]] = None


class TransactionResponse(TransactionBase):
    id: int
    status: TransactionStatus
    photos: Optional[List[str]] = None
    issued_by: int  # ID учителя
    issued_at: datetime
    returned_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionList(BaseModel):
    id: int
    textbook_title: str
    student_name: str
    transaction_type: TransactionType
    status: TransactionStatus
    issued_at: datetime
    returned_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BulkIssueRequest(BaseModel):
    textbook_ids: List[int] = Field(..., min_items=1)
    student_id: int
    notes: Optional[str] = Field(None, max_length=500)


class BulkReturnRequest(BaseModel):
    textbook_ids: List[int] = Field(..., min_items=1)
    notes: Optional[str] = Field(None, max_length=500) 