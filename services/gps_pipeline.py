import asyncio
import json
from typing import Any

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import GPSTrackEvent

GPS_QUEUE_KEY = 'gps:buffer'
BATCH_SIZE = 250


async def enqueue_gps_update(redis: Redis, payload: dict[str, Any]) -> None:
    await redis.rpush(GPS_QUEUE_KEY, json.dumps(payload, default=str))


async def flush_gps_buffer(redis: Redis, session: AsyncSession) -> int:
    raw_items = await redis.lrange(GPS_QUEUE_KEY, 0, BATCH_SIZE - 1)
    if not raw_items:
        return 0

    await redis.ltrim(GPS_QUEUE_KEY, len(raw_items), -1)
    events = []

    for raw in raw_items:
        data = json.loads(raw)
        events.append(
            GPSTrackEvent(
                tenant_id=data['tenant_id'],
                vehicle_id=data['vehicle_id'],
                latitude=data['latitude'],
                longitude=data['longitude'],
                heading=data.get('heading'),
                speed_kmh=data.get('speed_kmh'),
                battery_pct=data.get('battery_pct'),
                recorded_at=data['recorded_at'],
            )
        )

    session.add_all(events)
    await session.commit()
    return len(events)


async def periodic_flush(redis: Redis, session_factory) -> None:
    while True:
        async with session_factory() as session:
            inserted = await flush_gps_buffer(redis, session)
            if inserted:
                await session.flush()
        await asyncio.sleep(settings.gps_flush_seconds)
