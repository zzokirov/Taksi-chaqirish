"""
Farg'ona Viloyati Taksi Bot — Konfiguratsiya
"""
import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _get_db_url() -> str:
    url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/taxi_bot")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@dataclass
class Settings:
    """Bot sozlamalari."""
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_IDS: List[int] = field(default_factory=lambda: [
        int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
    ])
    DATABASE_URL: str = field(default_factory=_get_db_url)
    PAYMENT_CARD: str = os.getenv("PAYMENT_CARD", "8600 0000 0000 0000")
    PAYMENT_CARD_OWNER: str = os.getenv("PAYMENT_CARD_OWNER", "ADMIN")
    PAYMENT_AMOUNT: str = os.getenv("PAYMENT_AMOUNT", "50000")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "@admin")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()

