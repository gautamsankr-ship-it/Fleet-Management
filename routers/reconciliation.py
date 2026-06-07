from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db
from ml.reconciliation import match_transactions

router = APIRouter(prefix='/reconciliation', tags=['reconciliation'])


@router.post('/run')
async def run_reconciliation(tenant_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    results = await match_transactions(db, tenant_id)
    return {'tenant_id': tenant_id, 'matched': len(results), 'results': results}
