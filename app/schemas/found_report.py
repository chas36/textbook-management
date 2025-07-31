from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.found_report import FoundStatus


class FoundReportBase(BaseModel):
    textbook_id: int
    found_location: str = Field(..., min_length=5, max_length=200)
    description: Optional[str] = Field(None, max_length=500)


class FoundReportCreate(FoundReportBase):
    pass


class FoundReportUpdate(BaseModel):
    found_location: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[FoundStatus] = None
    notes: Optional[str] = Field(None, max_length=500)


class FoundReportResponse(FoundReportBase):
    id: int
    reported_by: int
    photos: Optional[List[str]] = None
    status: FoundStatus
    notes: Optional[str] = None
    returned_by: Optional[int] = None
    found_at: datetime
    returned_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FoundReportList(BaseModel):
    id: int
    textbook_title: str
    found_location: str
    status: FoundStatus
    found_at: datetime
    returned_at: Optional[datetime] = None

    class Config:
        from_attributes = True 