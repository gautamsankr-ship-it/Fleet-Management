from fastapi import APIRouter, Depends, HTTPException, Request

from dependencies import get_redis
from schemas import GPSUpdateCreate
from services.gps_pipeline import enqueue_gps_update

router = APIRouter(prefix='/gps', tags=['gps'])


@router.post('', status_code=202)
async def ingest_gps(update: GPSUpdateCreate, redis=Depends(get_redis)) -> dict:
    if update.latitude is None or update.longitude is None:
        raise HTTPException(status_code=400, detail='Latitude and longitude are required')

    await enqueue_gps_update(redis, update.dict())
    return {'status': 'accepted', 'vehicle_id': update.vehicle_id, 'recorded_at': str(update.recorded_at)}
