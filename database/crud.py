from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Task
from utils.time import now


async def get_or_create_user(session: AsyncSession, tg_id: int) -> User:
    """Возвращает пользователя по tg_id, создаёт если нет."""
    result = await session.execute(select(User).where(User.tg_id == tg_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(tg_id=tg_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


# ================= ЗАДАЧИ =================

async def create_task(
    session: AsyncSession,
    user_id: int,
    title: str,
    due_at: datetime | None = None,
    priority: str = "none",
    description: str | None = None,
) -> Task:
    task = Task(
        user_id=user_id,
        title=title,
        due_at=due_at,
        priority=priority,
        description=description,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def get_task(session: AsyncSession, user_id: int, task_id: int) -> Task | None:
    result = await session.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_tasks(session: AsyncSession, user_id: int) -> list[Task]:
    result = await session.execute(
        select(Task).where(Task.user_id == user_id).order_by(Task.due_at.asc().nulls_last(), Task.id.asc())
    )
    return list(result.scalars().all())


async def update_task_due(session: AsyncSession, task: Task, due_at: datetime | None) -> Task:
    task.due_at = due_at
    await session.commit()
    await session.refresh(task)
    return task


async def update_task_priority(session: AsyncSession, task: Task, priority: str) -> Task:
    task.priority = priority
    await session.commit()
    await session.refresh(task)
    return task


async def mark_task_done(session: AsyncSession, task: Task) -> Task:
    task.status = "done"
    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, task: Task) -> None:
    await session.delete(task)
    await session.commit()