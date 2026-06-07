import enum
from datetime import date

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class UserRoleType(str, enum.Enum):
    Admin = 'Admin'
    Vehicle_Owner = 'Vehicle_Owner'
    Driver = 'Driver'
    Conductor = 'Conductor'
    Staff = 'Staff'


class BillingMode(str, enum.Enum):
    per_run_day = 'per_run_day'
    monthly_lease = 'monthly_lease'


class VerificationStatus(str, enum.Enum):
    pending = 'pending'
    verified = 'verified'
    rejected = 'rejected'


class TenantRole(str, enum.Enum):
    Corporate = 'Corporate'
    School = 'School'
    Urban_Loop = 'Urban_Loop'
    Fleet_Admin = 'Fleet_Admin'


class AccountEntryType(str, enum.Enum):
    revenue = 'revenue'
    expense = 'expense'
    payroll = 'payroll'
    owner_share = 'owner_share'
    driver_payout = 'driver_payout'
    conductor_payout = 'conductor_payout'
    tax = 'tax'
    management = 'management'


class Tenant(Base):
    __tablename__ = 'tenants'

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    registration_number = Column(String(50), unique=True)
    tenant_role = Column(Enum(TenantRole), nullable=False, default=TenantRole.Fleet_Admin)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    users = relationship('User', back_populates='tenant')
    vehicles = relationship('Vehicle', back_populates='tenant')


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    phone_no = Column(String(15), unique=True, nullable=False)
    role_type = Column(Enum(UserRoleType), nullable=False)
    ssf_number = Column(String(50))
    tds_registration = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant = relationship('Tenant', back_populates='users')


class Vehicle(Base):
    __tablename__ = 'vehicles'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    license_plate_no = Column(String(20), unique=True, nullable=False)
    chassis_no = Column(String(50), unique=True, nullable=False)
    bluebook_expiry_gregorian = Column(Date, nullable=False)
    insurance_expiry_gregorian = Column(Date, nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant = relationship('Tenant', back_populates='vehicles')


class VehicleOwnerHistory(Base):
    __tablename__ = 'vehicle_owner_history'

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='RESTRICT'), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    assigned_date_gregorian = Column(Date, nullable=False)
    revoked_date_gregorian = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    vehicle = relationship('Vehicle')
    owner = relationship('User')


class VehicleOperatorHistory(Base):
    __tablename__ = 'vehicle_operator_history'

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='RESTRICT'), nullable=False)
    operator_id = Column(Integer, ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    operator_role = Column(Enum(UserRoleType), nullable=False)
    assigned_date_gregorian = Column(Date, nullable=False)
    revoked_date_gregorian = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    vehicle = relationship('Vehicle')
    operator = relationship('User')


class VehicleTenantHistory(Base):
    __tablename__ = 'vehicle_tenant_history'

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='RESTRICT'), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='RESTRICT'), nullable=False)
    assigned_date_gregorian = Column(Date, nullable=False)
    revoked_date_gregorian = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    vehicle = relationship('Vehicle')
    tenant = relationship('Tenant')


class VehicleBillingRate(Base):
    __tablename__ = 'vehicle_billing_rates'

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='RESTRICT'), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    start_date_gregorian = Column(Date, nullable=False)
    end_date_gregorian = Column(Date)
    mode = Column(Enum(BillingMode), nullable=False)
    mgmt_fee_rate = Column(Numeric(12, 2), nullable=False, default=1500.00)
    battery_fund_rate = Column(Numeric(12, 2), nullable=False, default=750.00)
    insurance_rate = Column(Numeric(12, 2), nullable=False, default=250.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    vehicle = relationship('Vehicle')
    tenant = relationship('Tenant')


class CostCenter(Base):
    __tablename__ = 'cost_centers'

    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(120), nullable=False)
    is_active = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    vehicle = relationship('Vehicle')


class DailyLogSheet(Base):
    __tablename__ = 'daily_log_sheets'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False)
    driver_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    conductor_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'))
    date_gregorian = Column(Date, nullable=False)
    nepali_year = Column(Integer, nullable=False)
    nepali_month = Column(Integer, nullable=False)
    trip_count = Column(Integer, nullable=False, default=0)
    start_km = Column(Numeric(10, 2), nullable=False)
    end_km = Column(Numeric(10, 2), nullable=False)
    total_km = Column(Numeric(10, 2), nullable=False)
    start_charging_pct = Column(Integer, nullable=False)
    end_charging_pct = Column(Integer, nullable=False)
    cash_collected = Column(Numeric(12, 2), nullable=False, default=0.00)
    qr_collected = Column(Numeric(12, 2), nullable=False, default=0.00)
    gross_collection = Column(Numeric(12, 2), nullable=False)
    ocr_image_url = Column(Text)
    status = Column(Enum(VerificationStatus), nullable=False, default=VerificationStatus.pending)
    remarks = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant = relationship('Tenant')
    vehicle = relationship('Vehicle')
    driver = relationship('User', foreign_keys=[driver_id])
    conductor = relationship('User', foreign_keys=[conductor_id])

    __table_args__ = (
        CheckConstraint('nepali_month BETWEEN 1 AND 12', name='daily_log_sheets_nepali_month_check'),
    )


class VariableExpense(Base):
    __tablename__ = 'variable_expenses'

    id = Column(Integer, primary_key=True)
    daily_log_sheet_id = Column(Integer, ForeignKey('daily_log_sheets.id', ondelete='CASCADE'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False)
    description = Column(Text, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    inferred_chart_code = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    daily_log_sheet = relationship('DailyLogSheet')


class RevenueLedgerEntry(Base):
    __tablename__ = 'revenue_ledger_entries'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False)
    entry_type = Column(Enum(AccountEntryType), nullable=False)
    reference_code = Column(String(80), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    details = Column(JSON, nullable=False, default={})
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant = relationship('Tenant')
    vehicle = relationship('Vehicle')


class EmployeePayrollProfile(Base):
    __tablename__ = 'employee_payroll_profiles'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    bank_name = Column(String(100), nullable=False)
    bank_account_no = Column(String(34), nullable=False)
    base_monthly_salary = Column(Numeric(12, 2), nullable=False)
    daily_allowance_rate = Column(Numeric(12, 2), nullable=False, default=0.00)
    ssf_eligible = Column(Integer, nullable=False, default=1)
    tds_percentage = Column(Numeric(5, 2), nullable=False, default=1.00)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship('User')


class MonthlyAttendanceRecord(Base):
    __tablename__ = 'monthly_attendance_records'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    nepali_year = Column(Integer, nullable=False)
    nepali_month = Column(Integer, nullable=False)
    days_present = Column(Integer, nullable=False, default=0)
    days_absent = Column(Integer, nullable=False, default=0)
    paid_leaves = Column(Integer, nullable=False, default=0)
    scanned_sheet_url = Column(Text)
    status = Column(Enum(VerificationStatus), nullable=False, default=VerificationStatus.pending)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship('User')

    __table_args__ = (
        CheckConstraint('nepali_month BETWEEN 1 AND 12', name='monthly_attendance_records_nepali_month_check'),
    )


class PayrollSlip(Base):
    __tablename__ = 'payroll_slips'

    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    nepali_year = Column(Integer, nullable=False)
    nepali_month = Column(Integer, nullable=False)
    gross_salary = Column(Numeric(12, 2), nullable=False)
    ssf_employee_deduction = Column(Numeric(12, 2), nullable=False)
    ssf_employer_contribution = Column(Numeric(12, 2), nullable=False)
    tds_deduction = Column(Numeric(12, 2), nullable=False)
    net_payout = Column(Numeric(12, 2), nullable=False)
    is_paid = Column(Integer, nullable=False, default=0)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship('User')

    __table_args__ = (
        CheckConstraint('nepali_month BETWEEN 1 AND 12', name='payroll_slips_nepali_month_check'),
    )


class GPSTrackEvent(Base):
    __tablename__ = 'gps_track_events'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False)
    latitude = Column(Numeric(10, 6), nullable=False)
    longitude = Column(Numeric(10, 6), nullable=False)
    heading = Column(SmallInteger)
    speed_kmh = Column(Numeric(6, 2))
    battery_pct = Column(SmallInteger)
    recorded_at = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant = relationship('Tenant')
    vehicle = relationship('Vehicle')


class BankTransaction(Base):
    __tablename__ = 'bank_transactions'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    transaction_date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    instrument_no = Column(String(60))
    issuer = Column(Text)
    narration = Column(Text)
    reference_code = Column(String(80))
    matched = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tenant = relationship('Tenant')


class TransactionReconciliation(Base):
    __tablename__ = 'transaction_reconciliations'

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False)
    bank_transaction_id = Column(Integer, ForeignKey('bank_transactions.id', ondelete='CASCADE'), nullable=False)
    daily_log_sheet_id = Column(Integer, ForeignKey('daily_log_sheets.id', ondelete='CASCADE'), nullable=False)
    confidence_score = Column(Numeric(5, 4), nullable=False)
    reconciled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    matched_by = Column(String(100), nullable=False, default='automated_ml')

    tenant = relationship('Tenant')
    bank_transaction = relationship('BankTransaction')
    daily_log_sheet = relationship('DailyLogSheet')
