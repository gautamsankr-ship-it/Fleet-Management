from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import async_session
from models import DailyLogSheet, VariableExpense
from schemas import DailyLogSheetCreate, DailyLogSheetOut, VariableExpenseCreate
from services.ledger import get_owner_share_for_vehicle, reconcile_daily_log_sheet
from utils.bs_converter import gregorian_to_nepali

router = APIRouter(prefix='/daily-log-sheets', tags=['ledger'])


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


@router.post('', response_model=DailyLogSheetOut)
async def create_daily_log_sheet(
    payload: DailyLogSheetCreate,
    variable_expenses: List[VariableExpenseCreate] | None = None,
    db: AsyncSession = Depends(get_db),
) -> DailyLogSheetOut:
    nepali_year, nepali_month, _ = gregorian_to_nepali(payload.date_gregorian)
    total_km = payload.end_km - payload.start_km
    gross_collection = payload.cash_collected + payload.qr_collected

    sheet = DailyLogSheet(
        tenant_id=payload.tenant_id,
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        conductor_id=payload.conductor_id,
        date_gregorian=payload.date_gregorian,
        nepali_year=nepali_year,
        nepali_month=nepali_month,
        trip_count=payload.trip_count,
        start_km=payload.start_km,
        end_km=payload.end_km,
        total_km=total_km,
        start_charging_pct=payload.start_charging_pct,
        end_charging_pct=payload.end_charging_pct,
        cash_collected=payload.cash_collected,
        qr_collected=payload.qr_collected,
        gross_collection=gross_collection,
        remarks=payload.remarks,
    )
    db.add(sheet)
    await db.commit()
    await db.refresh(sheet)

    expenses = []
    if variable_expenses:
        for expense_payload in variable_expenses:
            expense = VariableExpense(
                daily_log_sheet_id=sheet.id,
                vehicle_id=sheet.vehicle_id,
                description=expense_payload.description,
                amount=expense_payload.amount,
                inferred_chart_code=expense_payload.inferred_chart_code,
            )
            db.add(expense)
            expenses.append(expense)
        await db.commit()

    await reconcile_daily_log_sheet(db, sheet, expenses=expenses)
    return sheet


@router.get('/{vehicle_id}/owner-share', response_model=dict)
async def get_owner_share(vehicle_id: int, date_gregorian: str, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        date_value = date.fromisoformat(date_gregorian)
        owner_share = await get_owner_share_for_vehicle(db, vehicle_id, date_value)
        return {'vehicle_id': vehicle_id, 'date_gregorian': date_gregorian, 'owner_share': owner_share}
    except ValueError:
        raise HTTPException(status_code=400, detail='Invalid date format for owner share query')


@router.get('/{tenant_id}', response_model=List[DailyLogSheetOut])
async def list_daily_logs(tenant_id: int, db: AsyncSession = Depends(get_db)) -> List[DailyLogSheetOut]:
    stmt = select(DailyLogSheet).where(DailyLogSheet.tenant_id == tenant_id).order_by(DailyLogSheet.date_gregorian.desc())
    result = await db.execute(stmt)
    return result.scalars().all()
