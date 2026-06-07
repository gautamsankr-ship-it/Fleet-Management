import asyncio
import contextlib

from redis.asyncio import from_url
from fastapi import Depends, FastAPI

from config import settings
from dependencies import get_redis
from routers import gps_router, ledger_router, payroll_router, reconciliation_router
from services.gps_pipeline import periodic_flush
from db import async_session

app = FastAPI(title=settings.app_name)

app.include_router(gps_router)
app.include_router(ledger_router)
app.include_router(payroll_router)
app.include_router(reconciliation_router)


@app.on_event('startup')
async def startup_event() -> None:
    app.state.redis = await from_url(settings.redis_url, decode_responses=True)
    app.state.flush_task = asyncio.create_task(periodic_flush(app.state.redis, async_session))


@app.on_event('shutdown')
async def shutdown_event() -> None:
    flush_task = getattr(app.state, 'flush_task', None)
    if flush_task is not None:
        flush_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await flush_task
    redis = getattr(app.state, 'redis', None)
    if redis is not None:
        await redis.close()


@app.get('/')
async def health_check() -> dict:
    return {'status': 'ok', 'app': settings.app_name}


@app.get('/redis-status')
async def redis_status(redis=Depends(get_redis)) -> dict:
    ping = await redis.ping()
    return {'redis': ping}
