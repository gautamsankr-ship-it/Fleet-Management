from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db import async_session
from models import EmployeePayrollProfile, MonthlyAttendanceRecord, PayrollSlip
from schemas import PayrollSlipOut

router = APIRouter(prefix='/payroll', tags=['payroll'])


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


@router.post('/generate/{employee_id}/{nepali_year}/{nepali_month}', response_model=PayrollSlipOut)
async def generate_payroll_slip(
    employee_id: int,
    nepali_year: int,
    nepali_month: int,
    db: AsyncSession = Depends(get_db),
) -> PayrollSlipOut:
    profile_stmt = select(EmployeePayrollProfile).where(EmployeePayrollProfile.user_id == employee_id)
    profile_result = await db.execute(profile_stmt)
    profile = profile_result.scalar_one_or_none()

    if profile is None:
        raise HTTPException(status_code=404, detail='Payroll profile not found for employee')

    attendance_stmt = (
        select(MonthlyAttendanceRecord)
        .where(MonthlyAttendanceRecord.employee_id == employee_id)
        .where(MonthlyAttendanceRecord.nepali_year == nepali_year)
        .where(MonthlyAttendanceRecord.nepali_month == nepali_month)
    )
    attendance_result = await db.execute(attendance_stmt)
    attendance = attendance_result.scalar_one_or_none()

    if attendance is None:
        raise HTTPException(status_code=404, detail='Attendance record not found')

    payable_days = attendance.days_present + attendance.paid_leaves
    gross_salary = profile.base_monthly_salary + (profile.daily_allowance_rate * payable_days)
    ssf_employee = gross_salary * Decimal(str(settings.ssf_employee_rate)) if profile.ssf_eligible else Decimal('0.00')
    ssf_employer = gross_salary * Decimal(str(settings.ssf_employer_rate)) if profile.ssf_eligible else Decimal('0.00')
    tds = gross_salary * (profile.tds_percentage / Decimal('100.00'))
    net_payout = gross_salary - ssf_employee - tds

    slip = PayrollSlip(
        employee_id=employee_id,
        nepali_year=nepali_year,
        nepali_month=nepali_month,
        gross_salary=gross_salary,
        ssf_employee_deduction=ssf_employee,
        ssf_employer_contribution=ssf_employer,
        tds_deduction=tds,
        net_payout=net_payout,
        is_paid=False,
    )
    db.add(slip)
    await db.commit()
    await db.refresh(slip)
    return slip
