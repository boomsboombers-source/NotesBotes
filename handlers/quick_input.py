from aiogram import Router, F
from aiogram.types import Message

from database.db import async_session
from database.crud import get_or_create_user, create_task
from services.parser import parse_due
from utils.time import format_short

router = Router(name="quick_input")

# Кнопки меню — не перехватываем
MENU_BUTTONS = {
    "📋 Задачи", "📝 Заметки", "⏰ Напоминания", "📅 События",
    "✅ Трекер", "📋 Чек-листы", "📖 Инструкция", "⚙️ Настройки",
}


@router.message(F.text & ~F.text.startswith("/"))
async def quick_task(message: Message):
    text = message.text.strip()
    if text in MENU_BUTTONS:
        return
    # Игнорируем явные команды-префиксы других разделов
    if text.startswith(("!", "#")):
        return

    due, cleaned = parse_due(text)
    title = cleaned if cleaned else text

    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id)
        await create_task(session, user.id, title=title, due_at=due)

    when = f" ⏰ {format_short(due)}" if due else ""
    await message.answer(f"✅ Задача создана: <b>{title}</b>{when}")