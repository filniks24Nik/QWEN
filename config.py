import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Настройки канала
CHANNEL_NAME = "Мой AI Канал"
DEFAULT_LANGUAGE = "ru"
DEFAULT_QUALITY = "1080p"

# Приоритетные ниши 2026 (на основе анализа)
TOP_NICHES_2026 = [
    {
        "name": "Персональные финансы",
        "cpm": 18,
        "competition": "средняя",
        "description": "Инвестиции, бюджетирование, пассивный доход"
    },
    {
        "name": "AI инструменты и автоматизация",
        "cpm": 16,
        "competition": "низкая",
        "description": "Обзоры AI, рабочие процессы, туториалы"
    },
    {
        "name": "Заработок онлайн",
        "cpm": 17,
        "competition": "высокая",
        "description": "Фриланс, партнерки, бизнес-модели"
    },
    {
        "name": "Недвижимость",
        "cpm": 12,
        "competition": "средняя",
        "description": "Инвестиции в недвижимость, ипотека, аренда"
    },
    {
        "name": "Психология и саморазвитие",
        "cpm": 8,
        "competition": "низкая",
        "description": "Продуктивность, ментальное здоровье, привычки"
    }
]

