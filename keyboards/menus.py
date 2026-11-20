from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)


def main_menu() -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="📋 Задачи"), KeyboardButton(text="📝 Заметки")],
        [KeyboardButton(text="⏰ Напоминания"), KeyboardButton(text="📅 События")],
        [KeyboardButton(text="✅ Трекер"), KeyboardButton(text="📋 Чек-листы")],
        [KeyboardButton(text="📖 Инструкция"), KeyboardButton(text="⚙️ Настройки")],
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def tasks_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить", callback_data="task:add")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="task:refresh")],
    ])


def task_card(task_id: int, status: str = "pending") -> InlineKeyboardMarkup:
    rows = []
    if status == "pending":
        rows.append([InlineKeyboardButton(text="✅ Выполнено", callback_data=f"task:done:{task_id}")])
    rows.append([
        InlineKeyboardButton(text="🔴", callback_data=f"task:prio:{task_id}:high"),
        InlineKeyboardButton(text="🟡", callback_data=f"task:prio:{task_id}:medium"),
        InlineKeyboardButton(text="🟢", callback_data=f"task:prio:{task_id}:low"),
        InlineKeyboardButton(text="⚪", callback_data=f"task:prio:{task_id}:none"),
    ])
    rows.append([
        InlineKeyboardButton(text="➡️ На завтра", callback_data=f"task:tomorrow:{task_id}"),
        InlineKeyboardButton(text="📅 Дата", callback_data=f"task:setdate:{task_id}"),
    ])
    rows.append([InlineKeyboardButton(text="🗑 Удалить", callback_data=f"task:del:{task_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def task_back() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ К задачам", callback_data="task:list")],
    ])