from datetime import date
from decimal import Decimal
from typing import Iterable

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import (
    DailyLogSheet,
    RevenueLedgerEntry,
    VehicleBillingRate,
    VariableExpense,
)


async def get_active_billing_rate(session: AsyncSession, vehicle_id: int, effective_date: date) -> VehicleBillingRate | None:
    stmt = (
        select(VehicleBillingRate)
        .where(VehicleBillingRate.vehicle_id == vehicle_id)
        .where(VehicleBillingRate.start_date_gregorian <= effective_date)
        .where(
            (VehicleBillingRate.end_date_gregorian == None)
            | (VehicleBillingRate.end_date_gregorian >= effective_date)
        )
        .order_by(desc(VehicleBillingRate.start_date_gregorian))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _create_ledger_entry(tenant_id: int, vehicle_id: int, entry_type: str, amount: Decimal, reference_code: str, details: dict) -> RevenueLedgerEntry:
    return RevenueLedgerEntry(
        tenant_id=tenant_id,
        vehicle_id=vehicle_id,
        entry_type=entry_type,
        reference_code=reference_code,
        amount=amount,
        details=details,
    )


async def reconcile_daily_log_sheet(
    session: AsyncSession,
    daily_sheet: DailyLogSheet,
    expenses: Iterable[VariableExpense] = (),
) -> list[RevenueLedgerEntry]:
    billing_rate = await get_active_billing_rate(session, daily_sheet.vehicle_id, daily_sheet.date_gregorian)
    if billing_rate is None:
        raise ValueError('No active billing rate found for vehicle on that date')

    driver_amount = Decimal(settings.default_driver_payout)
    conductor_amount = Decimal(settings.default_conductor_payout)
    mgmt_amount = billing_rate.mgmt_fee_rate
    battery_amount = billing_rate.battery_fund_rate
    insurance_amount = billing_rate.insurance_rate
    variable_total = sum(exp.amount for exp in expenses) if expenses else Decimal('0.00')
    revenue = daily_sheet.gross_collection
    deductions = driver_amount + conductor_amount + mgmt_amount + battery_amount + insurance_amount + variable_total
    owner_share = max(revenue - deductions, Decimal('0.00'))

    entries = [
        _create_ledger_entry(
            tenant_id=daily_sheet.tenant_id,
            vehicle_id=daily_sheet.vehicle_id,
            entry_type='revenue',
            amount=revenue,
            reference_code=f'revenue:{daily_sheet.id}',
            details={'daily_log_sheet_id': daily_sheet.id},
        ),
        _create_ledger_entry(
            tenant_id=daily_sheet.tenant_id,
            vehicle_id=daily_sheet.vehicle_id,
            entry_type='driver_payout',
            amount=-driver_amount,
            reference_code=f'driver_payout:{daily_sheet.id}',
            details={'driver_id': daily_sheet.driver_id},
        ),
        _create_ledger_entry(
            tenant_id=daily_sheet.tenant_id,
            vehicle_id=daily_sheet.vehicle_id,
            entry_type='conductor_payout',
            amount=-conductor_amount,
            reference_code=f'conductor_payout:{daily_sheet.id}',
            details={'conductor_id': daily_sheet.conductor_id},
        ),
        _create_ledger_entry(
            tenant_id=daily_sheet.tenant_id,
            vehicle_id=daily_sheet.vehicle_id,
            entry_type='management',
            amount=-mgmt_amount,
            reference_code=f'management_fee:{daily_sheet.id}',
            details={'billing_rate_id': billing_rate.id},
        ),
        _create_ledger_entry(
            tenant_id=daily_sheet.tenant_id,
            vehicle_id=daily_sheet.vehicle_id,
            entry_type='expense',
            amount=-battery_amount,
            reference_code=f'battery_fund:{daily_sheet.id}',
            details={'billing_rate_id': billing_rate.id},
        ),
        _create_ledger_entry(
            tenant_id=daily_sheet.tenant_id,
            vehicle_id=daily_sheet.vehicle_id,
            entry_type='tax',
            amount=-insurance_amount,
            reference_code=f'insurance_rate:{daily_sheet.id}',
            details={'billing_rate_id': billing_rate.id},
        ),
    ]

    if variable_total > Decimal('0.00'):
        entries.append(
            _create_ledger_entry(
                tenant_id=daily_sheet.tenant_id,
                vehicle_id=daily_sheet.vehicle_id,
                entry_type='expense',
                amount=-variable_total,
                reference_code=f'variable_expense:{daily_sheet.id}',
                details={'variable_total': str(variable_total)},
            )
        )

    entries.append(
        _create_ledger_entry(
            tenant_id=daily_sheet.tenant_id,
            vehicle_id=daily_sheet.vehicle_id,
            entry_type='owner_share',
            amount=owner_share,
            reference_code=f'owner_share:{daily_sheet.id}',
            details={'owner_share': str(owner_share)},
        )
    )

    session.add_all(entries)
    await session.commit()
    return entries


async def get_owner_share_for_vehicle(session: AsyncSession, vehicle_id: int, date_value: date) -> Decimal:
    stmt = (
        select(func.sum(RevenueLedgerEntry.amount))
        .where(RevenueLedgerEntry.vehicle_id == vehicle_id)
        .where(RevenueLedgerEntry.entry_type == 'owner_share')
        .where(func.date(RevenueLedgerEntry.recorded_at) == date_value)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() or Decimal('0.00')
