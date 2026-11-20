from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from database.db import async_session
from database.crud import get_or_create_user
from keyboards.menus import main_menu
from texts.messages import welcome_text, SECTION_STUB

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message):
    async with async_session() as session:
        await get_or_create_user(session, message.from_user.id)
    await message.answer(welcome_text(), reply_markup=main_menu())


STUB_BUTTONS = {
    "📝 Заметки": "Заметки",
    "⏰ Напоминания": "Напоминания",
    "📅 События": "События",
    "✅ Трекер": "Трекер",
    "📋 Чек-листы": "Чек-листы",
    "📖 Инструкция": "Инструкция",
    "⚙️ Настройки": "Настройки",
}


@router.message(F.text.in_(STUB_BUTTONS.keys()))
async def stub_handler(message: Message):
    name = STUB_BUTTONS[message.text]
    await message.answer(SECTION_STUB.format(name=name))