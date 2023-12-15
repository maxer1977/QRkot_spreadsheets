from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, declared_attr, sessionmaker

from app.core.config import settings


class PreBase:
    # Во все таблицы будет добавлено поле ID.
    id = Column(Integer, primary_key=True)

    @declared_attr
    def __tablename__(cls):
        # Именем таблицы будет название модели в нижнем регистре
        return cls.__name__.lower()


Base = declarative_base(cls=PreBase)

engine = create_async_engine(settings.database_url)

async_session = AsyncSession(engine, expire_on_commit=False)

AsyncSessionLocal = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


# Асинхронный генератор сессий.
async def get_async_session():
    async with AsyncSessionLocal() as async_session:
        yield async_session
