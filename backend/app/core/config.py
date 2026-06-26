from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    GROQ_API_KEY: str = ""

    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "ai@yourdomain.com"

    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Agent settings
    AGENT_POLL_INTERVAL_MINUTES: int = 15
    MAX_CRAWL_PAGES: int = 30
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def google_redirect_uri(self) -> str:
        return f"{self.BACKEND_URL}/api/auth/google/callback"

    @property
    def google_calendar_redirect_uri(self) -> str:
        return f"{self.BACKEND_URL}/api/calendar/callback"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
