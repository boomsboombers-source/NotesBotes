import os
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///data/bot.db")

TIMEZONE = ZoneInfo("Asia/Novosibirsk")

MORNING_TIME = "08:00"
EVENING_TIME = "21:00"
TRACKER_TIME = "09:00"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан. Создай .env на основе .env.example")
