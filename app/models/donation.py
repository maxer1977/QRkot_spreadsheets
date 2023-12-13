from sqlalchemy import Column, ForeignKey, Integer, Text

# Импортируем базовый класс для моделей.
from app.models.charity_project import CustomBase


class Donation(CustomBase):
    comment = Column(Text)
    user_id = Column(Integer, ForeignKey("user.id"))
