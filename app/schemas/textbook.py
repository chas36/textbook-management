from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TextbookBase(BaseModel):
    subject: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    author: Optional[str] = Field(None, max_length=200)
    publisher: Optional[str] = Field(None, max_length=200)
    year: Optional[int] = Field(None, ge=1900, le=2030)
    isbn: Optional[str] = Field(None, pattern=r'^[\d-]{10,17}$')
    inventory_number: Optional[str] = Field(None, max_length=50)
    initial_condition: Optional[str] = Field(None, max_length=1000)


class TextbookCreate(TextbookBase):
    pass


class TextbookUpdate(BaseModel):
    subject: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, max_length=200)
    publisher: Optional[str] = Field(None, max_length=200)
    year: Optional[int] = Field(None, ge=1900, le=2030)
    isbn: Optional[str] = Field(None, pattern=r'^[\d-]{10,17}$')
    inventory_number: Optional[str] = Field(None, max_length=50)
    initial_condition: Optional[str] = Field(None, max_length=1000)
    current_condition: Optional[str] = Field(None, max_length=1000)
    is_active: Optional[bool] = None


class TextbookResponse(TextbookBase):
    id: int
    qr_code: str
    current_condition: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TextbookList(BaseModel):
    id: int
    qr_code: str
    subject: str
    title: str
    author: Optional[str] = None
    inventory_number: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class TextbookBulkCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    author: Optional[str] = Field(None, max_length=200)
    publisher: Optional[str] = Field(None, max_length=200)
    year: Optional[int] = Field(None, ge=1900, le=2030)
    isbn: Optional[str] = Field(None, pattern=r'^[\d-]{10,17}$')
    inventory_number_prefix: Optional[str] = Field(None, max_length=20)
    quantity: int = Field(..., ge=1, le=1000)
    initial_condition: Optional[str] = Field(None, max_length=1000) 