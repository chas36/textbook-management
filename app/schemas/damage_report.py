from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.damage_report import DamageType, DamageStatus


class DamageReportBase(BaseModel):
    textbook_id: int
    damage_type: DamageType
    description: str = Field(..., min_length=10, max_length=1000)


class DamageReportCreate(DamageReportBase):
    pass


class DamageReportUpdate(BaseModel):
    damage_type: Optional[DamageType] = None
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    status: Optional[DamageStatus] = None
    decision: Optional[str] = Field(None, max_length=500)


class DamageReportResponse(DamageReportBase):
    id: int
    reported_by: int
    photos: Optional[List[str]] = None
    status: DamageStatus
    decision: Optional[str] = None
    checked_by: Optional[int] = None
    reported_at: datetime
    checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DamageReportList(BaseModel):
    id: int
    textbook_title: str
    damage_type: DamageType
    status: DamageStatus
    reported_at: datetime
    checked_at: Optional[datetime] = None

    class Config:
        from_attributes = True 