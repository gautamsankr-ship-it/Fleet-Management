from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from config import settings


def get_engine() -> AsyncEngine:
    return create_async_engine(
        settings.database_url,
        echo=False,
        future=True,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


def get_session() -> sessionmaker[AsyncSession]:
    engine = get_engine()
    return sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async_session = get_session()
