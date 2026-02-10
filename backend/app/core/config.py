from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Q-Logic Dynamic Schema Orchestration"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/qlogic"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:postgres@db:5432/qlogic"
    CSV_SAMPLE_ROWS: int = 100
    MAX_CSV_SIZE_MB: int = 50
    CORS_ORIGINS: list[str] = ["http://localhost:4200"]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
