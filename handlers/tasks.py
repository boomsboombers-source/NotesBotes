from datetime import timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db import async_session
from database.crud import (
    get_or_create_user, get_user_tasks, get_task,
    mark_task_done, delete_task, update_task_due, update_task_priority,
    create_task,
)
from keyboards.menus import tasks_menu, task_card, task_back
from services.parser import parse_due
from utils.time import now, format_short

router = Router(name="tasks")

PRIO_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢", "none": "⚪"}


class AddTaskStates(StatesGroup):
    waiting_text = State()


class SetDateStates(StatesGroup):
    waiting_date = State()


def _task_line(t) -> str:
    prio = PRIO_EMOJI.get(t.priority, "⚪")
    if t.due_at:
        return f"{prio} {t.title} ⏰ {format_short(t.due_at)}"
    return f"{prio} {t.title}"


async def _render_tasks(message: Message, user_id: int):
    async with async_session() as session:
        tasks = await get_user_tasks(session, user_id)

    pending = [t for t in tasks if t.status == "pending"]
    if not pending:
        await message.answer("📋 Задач нет. Добавь первую!", reply_markup=tasks_menu())
        return

    cur = now()
    overdue, today, no_date = [], [], []
    for t in pending:
        if t.due_at is None:
            no_date.append(t)
        elif t.due_at < cur:
            overdue.append(t)
        elif t.due_at.date() == cur.date():
            today.append(t)
        else:
            no_date.append(t)

    lines = ["📋 <b>Твои задачи</b>\n"]
    if overdue:
        lines.append(f"🔴 <b>Просроченные ({len(overdue)})</b>")
        lines += [f"• {_task_line(t)}" for t in overdue]
        lines.append("")
    if today:
        lines.append(f"🟡 <b>На сегодня ({len(today)})</b>")
        lines += [f"• {_task_line(t)}" for t in today]
        lines.append("")
    if no_date:
        lines.append(f"🟢 <b>Без даты / будущие ({len(no_date)})</b>")
        lines += [f"• {_task_line(t)}" for t in no_date]

    await message.answer("\n".join(lines), reply_markup=tasks_menu())


@router.message(F.text == "📋 Задачи")
async def show_tasks(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id)
        uid = user.id
    await _render_tasks(message, uid)


@router.callback_query(F.data == "task:refresh")
async def refresh_tasks(cb: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, cb.from_user.id)
        uid = user.id
    await cb.message.edit_text("🔄 Обновляю...")
    await _render_tasks(cb.message, uid)
    await cb.answer()


@router.callback_query(F.data == "task:add")
async def add_task_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AddTaskStates.waiting_text)
    await cb.message.answer(
        "✍️ Пришли задачу текстом.\n"
        "Можно с датой: <code>завтра в 10 позвонить маме</code>\n"
        "Или просто: <code>купить хлеб</code>"
    )
    await cb.answer()


@router.message(AddTaskStates.waiting_text)
async def add_task_finish(message: Message, state: FSMContext):
    text = message.text.strip()
    due, cleaned = parse_due(text)
    title = cleaned if cleaned else text
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id)
        await create_task(session, user.id, title=title, due_at=due)
        uid = user.id
    await state.clear()
    when = f" ⏰ {format_short(due)}" if due else ""
    await message.answer(f"✅ Задача создана: <b>{title}</b>{when}")
    await _render_tasks(message, uid)


# ================= КАРТОЧКА ЗАДАЧИ =================

async def _show_card(target, task_id: int, user_id: int):
    async with async_session() as session:
        task = await get_task(session, user_id, task_id)
    if not task:
        text = "⚠️ Задача не найдена."
        if isinstance(target, CallbackQuery):
            await target.message.edit_text(text)
            await target.answer()
        else:
            await target.answer(text)
        return

    prio = PRIO_EMOJI.get(task.priority, "⚪")
    when = f"\n⏰ {format_short(task.due_at)}" if task.due_at else ""
    status = "✅ выполнена" if task.status == "done" else "⏳ в работе"
    text = f"{prio} <b>{task.title}</b>\n{status}{when}"
    kb = task_card(task.id, task.status)
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=kb)
        await target.answer()
    else:
        await target.answer(text, reply_markup=kb)


@router.message(F.text.startswith("/task_"))
async def show_card_cmd(message: Message):
    try:
        task_id = int(message.text.split("_", 1)[1])
    except (IndexError, ValueError):
        return
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id)
    await _show_card(message, task_id, user.id)


@router.callback_query(F.data == "task:list")
async def back_to_list(cb: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(session, cb.from_user.id)
        uid = user.id
    await cb.message.edit_text("📋 Список задач:")
    await _render_tasks(cb.message, uid)
    await cb.answer()


@router.callback_query(F.data.startswith("task:done:"))
async def cb_done(cb: CallbackQuery):
    task_id = int(cb.data.split(":")[2])
    async with async_session() as session:
        user = await get_or_create_user(session, cb.from_user.id)
        task = await get_task(session, user.id, task_id)
        if task:
            await mark_task_done(session, task)
    await cb.message.edit_text("✅ Задача выполнена!")
    await cb.answer()


@router.callback_query(F.data.startswith("task:del:"))
async def cb_del(cb: CallbackQuery):
    task_id = int(cb.data.split(":")[2])
    async with async_session() as session:
        user = await get_or_create_user(session, cb.from_user.id)
        task = await get_task(session, user.id, task_id)
        if task:
            await delete_task(session, task)
    await cb.message.edit_text("🗑 Задача удалена.")
    await cb.answer()


@router.callback_query(F.data.startswith("task:prio:"))
async def cb_prio(cb: CallbackQuery):
    _, _, task_id, prio = cb.data.split(":")
    task_id = int(task_id)
    async with async_session() as session:
        user = await get_or_create_user(session, cb.from_user.id)
        task = await get_task(session, user.id, task_id)
        if task:
            await update_task_priority(session, task, prio)
    await _show_card(cb, task_id, user.id)


@router.callback_query(F.data.startswith("task:tomorrow:"))
async def cb_tomorrow(cb: CallbackQuery):
    task_id = int(cb.data.split(":")[2])
    tomorrow = (now() + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
    async with async_session() as session:
        user = await get_or_create_user(session, cb.from_user.id)
        task = await get_task(session, user.id, task_id)
        if task:
            await update_task_due(session, task, tomorrow)
    await _show_card(cb, task_id, user.id)


@router.callback_query(F.data.startswith("task:setdate:"))
async def cb_setdate(cb: CallbackQuery, state: FSMContext):
    task_id = int(cb.data.split(":")[2])
    await state.update_data(setdate_task_id=task_id)
    await state.set_state(SetDateStates.waiting_date)
    await cb.message.answer("📅 Пришли новую дату: <code>завтра</code>, <code>25.11</code>, <code>25.11 15:00</code>")
    await cb.answer()


@router.message(SetDateStates.waiting_date)
async def setdate_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data.get("setdate_task_id")
    due, _ = parse_due(message.text)
    if not due:
        await message.answer("❌ Не понял дату. Попробуй: <code>завтра</code>, <code>25.11 15:00</code>")
        return
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id)
        task = await get_task(session, user.id, task_id)
        if task:
            await update_task_due(session, task, due)
    await state.clear()
    await message.answer(f"✅ Дата обновлена: ⏰ {format_short(due)}")