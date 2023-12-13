from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.utils import invest_it
from app.core.db import get_async_session
from app.core.user import current_superuser, current_user
from app.crud.donations import crud_donations
from app.models import User
from app.schemas.donations import (DonationCreate, DonationFulltDB,
                                   DonationShortDB)

router = APIRouter(
    tags=["Donations"],
)


@router.post(
    "/",
    response_model=DonationShortDB,
    response_model_exclude_none=True,
    dependencies=[Depends(current_user)],
)
async def create_donation(
    donation: DonationCreate,
    user: User = Depends(current_user),
    response_model_exclude={"close_date"},
    session: AsyncSession = Depends(get_async_session),
):
    """Создание пожертвования зарегистрированным пользователем."""
    new_donation = await crud_donations.create(donation, session, user)
    await invest_it(session)
    await session.refresh(new_donation)
    return new_donation


@router.get(
    "/",
    response_model=list[DonationFulltDB],
    response_model_exclude_none=True,
    dependencies=[Depends(current_superuser)],
)
async def get_all_donations(session: AsyncSession = Depends(get_async_session)):
    """Список всех пожертвований всех пользователей."""
    donations = await crud_donations.get_multi(session)
    return donations


@router.get(
    "/my",
    response_model=list[DonationShortDB],
    response_model_exclude_none=True,
    dependencies=[Depends(current_user)],
)
async def get_user_donations(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Список всех пожертвований авторизованного пользователей."""
    donations = await crud_donations.get_multi(session, user)
    return donations
