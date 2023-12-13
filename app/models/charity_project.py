from sqlalchemy import CheckConstraint, Column, String, Text

from .base import CustomBase


class CharityProject(CustomBase):
    name = Column(String(100), unique=True, nullable=False)
    description = Column(
        Text, CheckConstraint("LENGTH(description) >= 1"), nullable=False
    )
