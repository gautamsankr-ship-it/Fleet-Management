from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field("sqlite+aiosqlite:///./fleet.db", env="DATABASE_URL")
    redis_url: str = Field("redis://127.0.0.1:6379/0", env="REDIS_URL")
    app_name: str = Field("Ganga Mahasagar Fleet Backend", env="APP_NAME")
    nepali_timezone: str = Field("Asia/Kathmandu", env="NEPALI_TIMEZONE")
    gps_flush_seconds: int = Field(10, env="GPS_FLUSH_SECONDS")
    default_driver_payout: float = Field(1200.00, env="DEFAULT_DRIVER_PAYOUT")
    default_conductor_payout: float = Field(800.00, env="DEFAULT_CONDUCTOR_PAYOUT")
    ssf_employee_rate: float = Field(0.11, env="SSF_EMPLOYEE_RATE")
    ssf_employer_rate: float = Field(0.20, env="SSF_EMPLOYER_RATE")
    tds_default_pct: float = Field(1.00, env="TDS_DEFAULT_PCT")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
