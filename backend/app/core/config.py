from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    Every value has a local-dev default so `docker compose up` works out of
    the box, but production deployments MUST set real values via env vars or
    a mounted .env file.
    """

    # ── General ────────────────────────────────────────────────
    APP_NAME: str = "Q-Logic Dynamic Schema Orchestration"
    ENVIRONMENT: str = "development"  # development | staging | production
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    # ── Database (decomposed) ──────────────────────────────────
    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "qlogic"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_SSL_MODE: str = "prefer"  # disable | prefer | require | verify-ca

    # ── Connection pool tuning ─────────────────────────────────
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 40
    DB_POOL_RECYCLE: int = 3600  # seconds

    # ── Auth ───────────────────────────────────────────────────
    JWT_SECRET: str = "CHANGE-ME-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 480  # 8 hours

    # ── CSV Processing ─────────────────────────────────────────
    CSV_SAMPLE_ROWS: int = 100
    MAX_CSV_SIZE_MB: int = 50
    DATA_LOAD_BATCH_SIZE: int = 500

    # ── CORS ───────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["http://localhost:4200"]

    # ── Computed URLs ──────────────────────────────────────────

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?ssl={self.DB_SSL_MODE}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
