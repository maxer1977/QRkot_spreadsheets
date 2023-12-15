from typing import Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.api.utils as utils
from app.models import User


class CRUDBase:
    def __init__(self, model):
        self.model = model

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
    ):
        """Получение объекта по id."""
        db_obj = await session.execute(
            select(self.model).where(self.model.id == obj_id)
        )

        return db_obj.scalars().first()

    async def get_multi(
        self, session: AsyncSession, user: Optional[User] = None
    ):
        """Получение списка всех объектов."""
        request_text = select(self.model)

        if user is not None:
            request_text = request_text.where(self.model.user_id == user.id)

        db_objs = await session.execute(request_text)
        return db_objs.scalars().all()

    async def create(
        self, obj_in, session: AsyncSession, user: Optional[User] = None
    ):
        """Создание объекта."""
        obj_in_data = obj_in.dict()

        obj_in_data["create_date"] = utils.get_current_time()

        if user is not None:
            obj_in_data["user_id"] = user.id

        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj,
        obj_in,
        session: AsyncSession,
    ):
        """Редактирование объекта."""
        obj_data = jsonable_encoder(db_obj)

        update_data = obj_in.dict(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def remove(
        self,
        db_obj,
        session: AsyncSession,
    ):
        """Удаление объекта."""
        await session.delete(db_obj)
        await session.commit()
        return db_obj
