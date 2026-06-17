import os
from dotenv import load_dotenv

load_dotenv()


class _Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./tpv.db")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))
    GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


settings = _Settings()
