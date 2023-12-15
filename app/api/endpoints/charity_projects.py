from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils import (
    check_project_before_delete,
    check_project_before_update,
    check_project_name_before_create_update,
    invest_it,
)
from app.core.db import get_async_session
from app.core.user import current_superuser
from app.crud.charity_projects import crud_charity_projects
from app.schemas.charity_projects import (
    ProjectCreate,
    ProjectDB,
    ProjectUpdate,
)

router = APIRouter(
    tags=["Charity Project"],
)


@router.post(
    "/",
    response_model=ProjectDB,
    response_model_exclude_defaults=True,
    dependencies=(Depends(current_superuser),),
)
async def create_project(
    project: ProjectCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Создание нового проекта - только для суперюзеров."""
    await check_project_name_before_create_update(
        name=project.name, session=session
    )
    new_project = await crud_charity_projects.create(project, session)
    await invest_it(session)
    await session.refresh(new_project)
    return new_project


@router.get(
    "/",
    response_model=list[ProjectDB],
    response_model_exclude_none=True,
)
async def get_all_projects(
    session: AsyncSession = Depends(get_async_session),
):
    """Получение списка всех проектов - любой пользователь."""
    projects = await crud_charity_projects.get_multi(session)
    return projects


@router.patch(
    "/{project_id}",
    response_model=ProjectDB,
    dependencies=(Depends(current_superuser),),
)
async def update_project(
    project_id: int,
    obj_in: ProjectUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """Редактирование проекта - только для суперюзеров."""
    project = await crud_charity_projects.get(project_id, session)
    await check_project_before_update(project, project_id, obj_in, session)
    project = await crud_charity_projects.update(project, obj_in, session)
    return project


@router.delete(
    "/{project_id}",
    response_model=ProjectDB,
    dependencies=(Depends(current_superuser),),
)
async def remove_project(
    project_id: int,
    session: AsyncSession = Depends(get_async_session),
):
    """Удаление проекта - только для суперюзеров."""
    project = await check_project_before_delete(project_id, session)
    project = await crud_charity_projects.remove(project, session)
    return project
