from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Integer

from app.core.db import Base


class CustomBase(Base):
    __abstract__ = True
    __table_args__ = (CheckConstraint("full_amount >= invested_amount >= 0"),)

    full_amount = Column(Integer)
    invested_amount = Column(Integer, default=0)
    fully_invested = Column(Boolean, nullable=False, default=False)
    create_date = Column(DateTime, nullable=False)
    close_date = Column(DateTime)
