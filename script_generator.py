from google import genai
from config import GEMINI_API_KEY

MODEL_NAME = "gemini-2.5-flash"


class ScriptGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
        if not self.client:
            print("⚠️  GEMINI_API_KEY не задан — буду использовать шаблонные тексты.")

    def generate_script(self, topic, niche, duration_minutes=10):
        print(f"\n📝 Генерирую сценарий для: {topic}")

        if not self.client:
            return self._fallback_script(topic, niche)

        prompt = f"""
Ты — сценарист YouTube-канала про технологии. Твоя задача — создать КОНКРЕТНЫЙ,
насыщенный фактами сценарий. Зритель должен УСЛЫШАТЬ НАЗВАНИЯ инструментов,
цифры и примеры. Общие слова запрещены.

НИША: {niche}
ТЕМА: {topic}

ГЛАВНОЕ ТРЕБОВАНИЕ:
Если тема про инструменты, сервисы или нейросети — ты ОБЯЗАН называть их
ПО ИМЕНАМ. Например: ChatGPT, Claude, Gemini, Midjourney, Perplexity,
Runway, Synthesia, Notion AI, Copy.ai, ElevenLabs и т.д.
НЕ пиши «один из инструментов» — пиши название. Это НЕ реклама, это информация.

СТРУКТУРА (обязательно соблюдай):

1. Сцена 1 (крючок): удивительный факт или цифра по теме. 5-7 предложений.
2. Сцены 2-3 (проблема): почему тема важна, что теряет человек без неё.
3. Основная часть — по одной сцене на КАЖДЫЙ инструмент/пункт из темы.
   Если тема «Топ-5 инструментов» — 5 сцен с инструментами.
   Если тема «10 нейросетей» — 10 сцен.
   Каждая такая сцена:
   - Название инструмента (имя!)
   - Что он делает (конкретно)
   - Кому подходит
   - Цена (бесплатно / от X$)
   - Пример: «Программист Иван сократил время на код в 2 раза»
4. Сцена-практика: что делать прямо сегодня, пошагово.
5. Последняя сцена: призыв подписаться.

ФОРМАТ ОТВЕТА (строго):

[SCENE 1]
VISUAL: 3-5 english words describing the visual subject of THIS scene
TEXT: Текст сцены, 5-7 предложений.

[SCENE 2]
VISUAL: ...
TEXT: ...

... и так далее.

ПРАВИЛА ДЛЯ ТЕКСТА:
1. КАЖДАЯ сцена про инструмент — НАЧИНАЕТСЯ С НАЗВАНИЯ этого инструмента.
   Например: «Первое место — ChatGPT. Это...»
2. ЦИФРЫ обязательны: сколько стоит, сколько экономит, сколько пользователей.
3. ПРИМЕРЫ обязательны: «маркетолог Анна использует X для Y и получает Z».
4. ЗАПРЕЩЕНЫ фразы:
   - «сегодня мы поговорим о...»
   - «это очень важно»
   - «в современном мире»
   - «многие эксперты считают»
   - «не секрет, что»
   - «стоит отметить, что»
5. РАЗГОВОРНЫЙ СТИЛЬ, как будто объясняешь другу.
6. 5-7 предложений на сцену.
7. НЕ используй маркдаун (**, ##, ---, ```).

ПРАВИЛА ДЛЯ VISUAL:
1. На английском, 3-5 слов.
2. КОНКРЕТНЫЙ визуальный объект из TEXT этой сцены.
3. Для сцены про ChatGPT → «person typing laptop screen».
4. НЕ используй: technology, business, future, concept.
5. НЕ используй бренды в VISUAL — только общий образ
   (для ChatGPT → «person typing», для Midjourney → «digital art painting»).

ВЕРНИ ТОЛЬКО СЦЕНЫ. Без пояснений.
"""

        try:
            response = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            script = response.text
            print(f"✅ Сценарий сгенерирован ({len(script)} символов)")
            return script
        except Exception as e:
            print(f"❌ Ошибка генерации: {e}")
            return self._fallback_script(topic, niche)

    def _fallback_script(self, topic, niche):
        return f"""[SCENE 1]
VISUAL: person typing laptop
TEXT: Привет! Сегодня разберём {topic}. Ты узнаешь конкретные инструменты с названиями, ценами и примерами.

[SCENE 2]
VISUAL: data charts screen
TEXT: Первый инструмент — ChatGPT от OpenAI. Это чат-бот на базе GPT-4, работает в браузере и приложении. Бесплатная версия доступна всем, платная от 20$ в месяц. Копирайтер Сергей сократил время на статьи в 3 раза.

[SCENE 3]
VISUAL: digital art painting
TEXT: Второй — Midjourney. Генерирует изображения по тексту за 30 секунд. Стоит от 10$ в месяц. Дизайнер Ольга делает обложки для блога за 5 минут вместо 2 часов.

[SCENE 4]
VISUAL: subscribe youtube button
TEXT: Если было полезно — подписывайся. В следующих видео разберём ещё больше инструментов.
"""

    def generate_title_and_description(self, script, niche):
        print("\n🎬 Генерирую название и описание...")

        if not self.client:
            return {
                "title": f"{niche}: обзор",
                "description": script[:200],
                "tags": [niche, "youtube", "автоматизация"],
            }

        prompt = f"""
На основе сценария создай метаданные для YouTube.

НИША: {niche}
СЦЕНАРИЙ (фрагмент): {script[:1500]}

ФОРМАТ ОТВЕТА (строго):

НАЗВАНИЕ: цепляющее название до 60 символов, с цифрой или интригой
ОПИСАНИЕ: описание 100-200 слов с ключевыми словами и именами инструментов
ТЕГИ: тег1, тег2, тег3, ... (10 штук)
"""

        try:
            response = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            result = response.text
            title = ""
            description = ""
            tags = []
            for line in result.strip().split("\n"):
                if line.startswith("НАЗВАНИЕ:"):
                    title = line.replace("НАЗВАНИЕ:", "").strip()
                elif line.startswith("ОПИСАНИЕ:"):
                    description = line.replace("ОПИСАНИЕ:", "").strip()
                elif line.startswith("ТЕГИ:"):
                    tags_str = line.replace("ТЕГИ:", "").strip()
                    tags = [t.strip() for t in tags_str.split(",") if t.strip()]

            if not title:
                title = f"{niche}: обзор"
            print(f"✅ Название: {title}")
            return {
                "title": title,
                "description": description or script[:200],
                "tags": tags or [niche, "youtube", "автоматизация"],
            }
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            return {
                "title": f"{niche}: обзор",
                "description": script[:200],
                "tags": [niche, "youtube", "автоматизация"],
            }
