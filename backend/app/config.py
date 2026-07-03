from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    STUDIO_ID: str = "00000000-0000-0000-0000-000000000001"
    DATABASE_URL: str = "postgresql+asyncpg://rcuser:rcpassword@db:5432/registro_contabilita"
    JWT_SECRET: str = "changeme_in_production_use_long_random_string"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480
    SEED_ADMIN_EMAIL: str = "admin@studio-rossi.it"
    SEED_ADMIN_PASSWORD: str = "Admin2024!Secure"
    ALLOWED_ORIGINS: str = "*"

    model_config = {"env_file": ".env"}

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        # Railway/Render forniscono postgresql:// o postgres:// — SQLAlchemy async richiede il driver asyncpg
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://") :]
        if v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://") :]
        return v


settings = Settings()
