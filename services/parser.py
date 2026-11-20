import re
from datetime import datetime, timedelta
from utils.time import now

_RE_TIME = re.compile(r"(\d{1,2}):(\d{2})")
_RE_DATE = re.compile(r"(\d{1,2})\.(\d{1,2})")
_RE_IN = re.compile(r"через\s+(\d+)\s*(минут|мин|час|ч)", re.IGNORECASE)


def parse_due(text: str) -> tuple[datetime | None, str]:
    """
    Ищет дату/время в тексте и возвращает (due_at, очищенный_текст).
    Понимает: 'завтра', 'послезавтра', 'сегодня', 'через N минут/часов',
    'ДД.ММ', 'ДД.ММ ЧЧ:ММ', 'ЧЧ:ММ' (сегодня/завтра, если время прошло).
    """
    base = now()
    due = None
    cleaned = text

    # 1. "через N минут/часов"
    m = _RE_IN.search(cleaned)
    if m:
        n = int(m.group(1))
        unit = m.group(2).lower()
        if unit.startswith("мин"):
            due = base + timedelta(minutes=n)
        else:
            due = base + timedelta(hours=n)
        cleaned = cleaned[:m.start()] + cleaned[m.end():]
        return due, cleaned.strip(" ,")

    # 2. "сегодня" / "завтра" / "послезавтра"
    low = cleaned.lower()
    day_offset = None
    for word, offset in (("послезавтра", 2), ("завтра", 1), ("сегодня", 0)):
        if word in low:
            day_offset = offset
            cleaned = re.sub(word, "", cleaned, count=1, flags=re.IGNORECASE)
            break

    # 3. Дата "ДД.ММ" и время "ЧЧ:ММ"
    date_match = _RE_DATE.search(cleaned)
    time_match = _RE_TIME.search(cleaned)

    target_date = None
    target_time = None

    if date_match:
        day, month = int(date_match.group(1)), int(date_match.group(2))
        year = base.year
        try:
            target_date = datetime(year, month, day)
            if target_date.date() < base.date():
                target_date = datetime(year + 1, month, day)
        except ValueError:
            return None, text
        cleaned = cleaned[:date_match.start()] + cleaned[date_match.end():]

    if time_match:
        hh, mm = int(time_match.group(1)), int(time_match.group(2))
        if 0 <= hh < 24 and 0 <= mm < 60:
            target_time = (hh, mm)
        cleaned = cleaned[:time_match.start()] + cleaned[time_match.end():]

    # Собираем итог
    if target_date is not None:
        if target_time:
            due = target_date.replace(hour=target_time[0], minute=target_time[1])
        else:
            due = target_date.replace(hour=9, minute=0)
    elif day_offset is not None:
        d = (base + timedelta(days=day_offset))
        if target_time:
            due = d.replace(hour=target_time[0], minute=target_time[1], second=0, microsecond=0)
        else:
            due = d.replace(hour=9, minute=0, second=0, microsecond=0)
    elif target_time:
        # только время — сегодня, а если прошло — завтра
        d = base.replace(hour=target_time[0], minute=target_time[1], second=0, microsecond=0)
        if d < base:
            d += timedelta(days=1)
        due = d

    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.-")
    return due, cleaned if cleaned else text