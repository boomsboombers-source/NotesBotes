from utils.time import now, format_date

WELCOME = (
    "👋 Привет! Я твой личный ежедневник.\n\n"
    "📅 Сегодня: {date}\n\n"
    "Выбери раздел на клавиатуре ниже."
)

SECTION_STUB = "🚧 Раздел «{name}» в разработке. Скоро здесь всё будет."


def welcome_text() -> str:
    return WELCOME.format(date=format_date(now()))