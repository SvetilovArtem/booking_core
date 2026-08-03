from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

DATABASE_URL = "postgresql+asyncpg://booking_user:password123@localhost:5433/booking_db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

metadata = MetaData()

class Base(DeclarativeBase):
    metadata = metadata

async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session