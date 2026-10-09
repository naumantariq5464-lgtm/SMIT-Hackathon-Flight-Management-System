from typing import List, Union, Optional
from pydantic import EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Flight Management System API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Database (Neon PostgreSQL connection string)
    DATABASE_URL: str = "postgresql+asyncpg://neondb_owner:password@ep-test.us-east-2.aws.neon.tech/neondb?ssl=require"

    # Security
    JWT_SECRET_KEY: str = "super-secret-flight-management-jwt-signing-key-change-in-production-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    # Holds & Policies
    PRICE_HOLD_EXPIRE_MINUTES: int = 15
    SEAT_HOLD_EXPIRE_MINUTES: int = 10
    DEFAULT_OVERBOOKING_POLICY: str = "HARD_LIMIT"  # HARD_LIMIT or BUFFER_ALLOWED

    # Default Super Admin Seed Credentials
    FIRST_SUPERADMIN_EMAIL: EmailStr = "admin@gmail.com"
    FIRST_SUPERADMIN_PASSWORD: str = "123@#$"

    # SMTP Configuration
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # LLM Configuration
    GROQ_API_KEY: Optional[str] = None

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
