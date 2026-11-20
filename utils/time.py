from datetime import datetime
from config import TIMEZONE


def now() -> datetime:
    """Текущее время в часовом поясе бота."""
    return datetime.now(TIMEZONE)


def format_date(dt: datetime) -> str:
    """19.11.2026"""
    return dt.strftime("%d.%m.%Y")


def format_time(dt: datetime) -> str:
    """15:00"""
    return dt.strftime("%H:%M")


def format_datetime(dt: datetime) -> str:
    """19.11.2026 15:00"""
    return dt.strftime("%d.%m.%Y %H:%M")


def format_short(dt: datetime) -> str:
    """19.11 15:00"""
    return dt.strftime("%d.%m %H:%M")