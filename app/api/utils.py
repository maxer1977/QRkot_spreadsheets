from datetime import datetime
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy import asc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.crud.charity_projects as crud
from app.models import CharityProject, Donation
from app.schemas.charity_projects import ProjectUpdate


def get_current_time():
    """Получение текущих даты и времени."""
    return datetime.now()


async def check_project_name_before_create_update(
    name: str,
    session: AsyncSession,
):
    """Проверка имени проекта на уникальвность."""
    db_obj = await crud.crud_charity_projects.get_project_by_name(
        name=name, session=session
    )
    if db_obj is not None:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Проект с таким именем уже существует!",
        )


async def check_project_id(
    project_id: int,
    session: AsyncSession,
):
    """Проверка проекта по id."""
    project = await crud.crud_charity_projects.get(project_id, session)
    if project is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail=f"Проект {project_id} не найден!"
        )
    return project


async def check_project_before_update(
    project: CharityProject,
    project_id: int,
    obj_in: ProjectUpdate,
    session: AsyncSession,
):
    """Проверка проекта перед обновлением."""
    # Проверка существования проекта с таким id
    await check_project_id(project_id, session)
    # Проверка статуса "открыт/закрыт" для инвестирования
    if project.fully_invested is True or project.close_date:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Закрытый проект нельзя редактировать!",
        )
    # Проверка, что название проекта остается уникальным
    if obj_in.name is not None and obj_in.name != project.name:
        await check_project_name_before_create_update(name=obj_in.name, session=session)
    # Проверка, что новая сумма проекта не меньше зачисленных средств
    if obj_in.full_amount and project.invested_amount > obj_in.full_amount:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Новая сумма проекта {obj_in.full_amount} не может быть меньше внесенной - {project.invested_amount}!",
        )


async def check_project_before_delete(project_id, session):
    """Проверка проекта перед удалением."""
    project = await check_project_id(project_id, session)
    if project.invested_amount > 0:
        await crud.crud_charity_projects.close_project(project, session)
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="В проект были внесены средства, не подлежит удалению!",
        )
    return project


async def invest_it(
    session: AsyncSession,
):
    """Функция инвестирования."""
    # Выборка активных проектов с сортировкой
    project_objs = await session.execute(
        select(CharityProject)
        .where(CharityProject.close_date.is_(None))
        .order_by(asc(CharityProject.create_date))
    )
    project_objs = project_objs.scalars().all()

    # Подсчет стоимости активных проектов и суммы
    # финансирования
    project_sum = await session.execute(
        select(
            func.sum(CharityProject.full_amount),
            func.sum(CharityProject.invested_amount),
        ).where(CharityProject.close_date.is_(None))
    )
    project_sum = project_sum.fetchall()
    project_full = 0 if project_sum[0][0] is None else project_sum[0][0]
    project_invested = 0 if project_sum[0][1] is None else project_sum[0][1]

    # Вычисление суммы необходимого финансирования
    to_invest = project_full - project_invested

    # Выборка активных пожертвований с сортировкой
    donation_objs = await session.execute(
        select(Donation)
        .where(Donation.close_date.is_(None))
        .order_by(asc(Donation.create_date))
    )
    donation_objs = donation_objs.scalars().all()

    # Подсчет сумм полученных и распределенных
    # пожертвований
    donation_sum = await session.execute(
        select(
            func.sum(Donation.full_amount), func.sum(Donation.invested_amount)
        ).where(Donation.close_date.is_(None))
    )
    donation_sum = donation_sum.fetchall()
    donation_full = 0 if donation_sum[0][0] is None else donation_sum[0][0]
    donation_invested = 0 if donation_sum[0][1] is None else donation_sum[0][1]

    # Вычисление суммы доступного финансирования
    to_be_invested = donation_full - donation_invested

    # Обработка списка проектов
    for project in project_objs:
        # Распределение финансирования ведется, пока
        # есть потребность и доступные средства
        if to_be_invested > 0 and to_invest > 0:
            # Вычисление необходимого финансирования на проект
            project_to_invest = project.full_amount - project.invested_amount
            # Если сумма инвестиций для проекта меньше доступной суммы финансирования
            if project_to_invest <= to_be_invested:
                # Увеличиваем в проекте сумму "invested_amount" = "full_amount"
                setattr(project, "invested_amount", project.full_amount)
                setattr(project, "close_date", get_current_time())
                setattr(project, "fully_invested", True)
                # Уменьшаем сумму требуемого финансирования (на все проекты)
                to_invest = to_invest - project_to_invest
                # Уменьшаем сумму доступного финансирования
                to_be_invested = to_be_invested - project_to_invest
                session.add(project)
            # Если сумма инвестиций для проекта больше доступной суммы финансирования
            else:
                # Увеличиваем баланс полученного финансирования на всю оставшуюся
                # сумму пожертвований
                setattr(
                    project, "invested_amount", project.invested_amount + to_be_invested
                )
                session.add(project)
                # И прекращаем распределение пожертвований по проектам
                break
        # Если потребность в финансировании или пожертвования закончились
        else:
            # Прекращаем распределение пожертвований по проектам
            break
    # Восстанавливаем первоначальные значение суммы доступных пожертвований
    to_be_invested = donation_full - donation_invested
    # и сумму потребности в инвестировании
    to_invest = project_full - project_invested
    # Определяем на какую величину будет уменьшена сумма доступных пожертвований
    to_be_invested = min(to_be_invested, to_invest)

    # Обработка списка пожертвований
    for donation in donation_objs:
        # Вычисление доступную сумму пожертвования
        donation_to_be_invested = donation.full_amount - donation.invested_amount
        # Если сумма пожертвования меньше доступной суммы пожертвований
        if donation_to_be_invested <= to_be_invested:
            # Увеличиваем в пожертвовании сумму "invested_amount" = "full_amount"
            setattr(donation, "invested_amount", donation.full_amount)
            setattr(donation, "close_date", get_current_time())
            setattr(donation, "fully_invested", True)
            # Увеличиваем в проекте сумму "invested_amount" = "full_amount"
            to_be_invested = to_be_invested - donation_to_be_invested
            # print("Осталось распределить пожертвований - ", to_be_invested)
            session.add(donation)

        else:
            setattr(
                donation, "invested_amount", donation.invested_amount + to_be_invested
            )
            session.add(donation)
            break

    await session.commit()
