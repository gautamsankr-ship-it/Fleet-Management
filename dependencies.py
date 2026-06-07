from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from db import async_session


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


def get_redis(request: Request):
    redis = getattr(request.app.state, 'redis', None)
    if redis is None:
        raise HTTPException(status_code=503, detail='Redis is not initialized')
    return redis
