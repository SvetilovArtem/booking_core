from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Путь к корню проекта
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Bot
    BOT_TOKEN: str
    BUSINESS_ID: int

    # Database
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int

    # App
    LOG_LEVEL: str = "INFO"

    # Строка подключения к БД
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # URL для Redis
    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

settings = Settings()