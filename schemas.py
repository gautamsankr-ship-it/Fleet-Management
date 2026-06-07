from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, constr


class TenantBase(BaseModel):
    name: str = Field(..., max_length=150)
    registration_number: Optional[str] = Field(None, max_length=50)
    tenant_role: Optional[str] = 'Fleet_Admin'


from datetime import datetime

class GPSUpdateCreate(BaseModel):
    tenant_id: int
    vehicle_id: int
    latitude: Decimal
    longitude: Decimal
    heading: Optional[int] = None
    speed_kmh: Optional[Decimal] = None
    battery_pct: Optional[int] = None
    recorded_at: datetime


class DailyLogSheetCreate(BaseModel):
    tenant_id: int
    vehicle_id: int
    driver_id: Optional[int]
    conductor_id: Optional[int]
    date_gregorian: date
    start_km: Decimal
    end_km: Decimal
    start_charging_pct: int
    end_charging_pct: int
    trip_count: int = 0
    cash_collected: Decimal = Decimal('0.00')
    qr_collected: Decimal = Decimal('0.00')
    remarks: Optional[str] = None


class VariableExpenseCreate(BaseModel):
    description: str
    amount: Decimal
    inferred_chart_code: Optional[str] = None


class DailyLogSheetOut(BaseModel):
    id: int
    tenant_id: int
    vehicle_id: int
    driver_id: Optional[int]
    conductor_id: Optional[int]
    date_gregorian: date
    nepali_year: int
    nepali_month: int
    trip_count: int
    start_km: Decimal
    end_km: Decimal
    total_km: Decimal
    cash_collected: Decimal
    qr_collected: Decimal
    gross_collection: Decimal
    status: str

    class Config:
        orm_mode = True


class PayrollSlipOut(BaseModel):
    employee_id: int
    nepali_year: int
    nepali_month: int
    gross_salary: Decimal
    ssf_employee_deduction: Decimal
    ssf_employer_contribution: Decimal
    tds_deduction: Decimal
    net_payout: Decimal
    is_paid: bool

    class Config:
        orm_mode = True


class BankTransactionCreate(BaseModel):
    tenant_id: int
    transaction_date: date
    amount: Decimal
    instrument_no: Optional[str] = None
    issuer: Optional[str] = None
    narration: Optional[str] = None
    reference_code: Optional[str] = None


class TransactionMatchOut(BaseModel):
    bank_transaction_id: int
    daily_log_sheet_id: int
    confidence_score: Decimal
    matched_by: str

    class Config:
        orm_mode = True
