"""Конфигурация подключения к БД. SQLite для разработки."""

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "booking.db")

DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

metadata = MetaData()


class Base(DeclarativeBase):
    metadata = metadata


async def get_db() -> AsyncSession:
    """Зависимость для получения сессии БД в роутах."""
    async with async_session() as session:
        yield session