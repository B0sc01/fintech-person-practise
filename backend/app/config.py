from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    APP_NAME: str = "Fintech Quant System"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///" + str(
        Path(__file__).parent.parent.parent / "data" / "fintech.db"
    )

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
