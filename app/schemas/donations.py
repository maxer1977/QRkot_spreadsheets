from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Extra, Field


class DonationCreate(BaseModel):
    full_amount: int = Field(..., gt=0)
    comment: Optional[str]

    class Config:
        extra = Extra.forbid


class DonationShortDB(DonationCreate):
    id: int
    create_date: Optional[datetime]

    class Config:
        orm_mode = True


class DonationFulltDB(DonationShortDB):
    user_id: int
    invested_amount: int
    fully_invested: bool
    # убрано по условиям теста
    # close_date: Optional[datetime]

    class Config:
        orm_mode = True
