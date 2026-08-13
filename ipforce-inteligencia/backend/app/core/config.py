from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "IPForce Inteligencia"
    DATABASE_URL: str = "postgresql+asyncpg://ipforce:ipforce_secret@db:5432/ipforce"
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    PABX_BASE_URL: str = ""
    PABX_API_KEY: str = ""

    OLLAMA_HOST: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    WHISPER_MODEL: str = "large-v2"
    WHISPER_DEVICE: str = "cuda"
    WHISPER_COMPUTE_TYPE: str = "float16"
    HF_TOKEN: str = ""

    SYNC_INTERVAL_MINUTES: int = 5
    MAX_AUDIO_AGE_HOURS: int = 24

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
