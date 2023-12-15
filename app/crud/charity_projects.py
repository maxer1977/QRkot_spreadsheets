from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.api.utils as utils
from app.crud.base import CRUDBase
from app.models.charity_project import CharityProject


class CRUDProject(CRUDBase):
    async def get_project_by_name(
        self,
        name: str,
        session: AsyncSession,
    ):
        """Получение проекта по его имени."""
        db_obj = await session.execute(
            select(self.model).where(self.model.name == name)
        )
        db_obj = db_obj.scalars().first()
        return db_obj

    async def close_project(
        self,
        db_obj: CharityProject,
        session: AsyncSession,
    ):
        """Закрытие проекта - установка даты закрытия."""
        if db_obj.close_date is None:
            print(db_obj.close_date)
            setattr(db_obj, "close_date", utils.get_current_time())
            session.add(db_obj)
            await session.commit()
            await session.refresh(db_obj)

    async def get_projects_by_completion_rate(
        self, session: AsyncSession
    ) -> list[list]:
        """Выборка закрытых проектов."""
        project_objs = await session.execute(
            select(CharityProject).where(CharityProject
                                         .close_date.isnot(None))
        )
        project_objs = project_objs.scalars().all()

        project_list = []

        for project in project_objs:
            project_list.append(
                [
                    project.name,
                    project.close_date - project.create_date,
                    str(project.close_date - project.create_date),
                    project.description,
                    project.invested_amount,
                ]
            )

        project_list = sorted(project_list, key=lambda x: x[1])
        return project_list


crud_charity_projects = CRUDProject(CharityProject)
