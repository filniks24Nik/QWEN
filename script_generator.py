import os
from openai import OpenAI

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL_NAME = "openai/gpt-oss-120b"


class ScriptGenerator:
    def __init__(self):
        self.client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        if not self.client:
            print("⚠️  GROQ_API_KEY не задан — буду использовать шаблонные тексты.")

    def _generate(self, prompt):
        try:
            r = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=8000,
            )
            print(f"   (модель: {MODEL_NAME})")
            return r.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Groq ошибка: {e}")
            return None

    def generate_script(self, topic, niche, duration_minutes=10):
        print(f"\n📝 Генерирую сценарий для: {topic}")
        if not self.client:
            return self._fallback_script(topic, niche)

        prompt = f"""Ты — сценарист YouTube-канала про технологии. Создай КОНКРЕТНЫЙ сценарий.
Общие фразы ЗАПРЕЩЕНЫ. Только факты, названия, цифры, примеры.

НИША: {niche}
ТЕМА: {topic}
ДЛИТЕЛЬНОСТЬ: примерно {duration_minutes} минут

КРИТИЧЕСКИ ВАЖНО:

1. ЕСЛИ В ТЕМЕ ЕСТЬ ЧИСЛО (Топ-5, Топ-3, 10 штук):
   - Назови РОВНО столько конкретных инструментов/пунктов.
   - На КАЖДЫЙ инструмент — ОТДЕЛЬНЫЙ GROUP с его ИМЕНЕМ.
   - Название инструмента — ПЕРВОЕ СЛОВО первой сцены этой группы.
   - НЕ переходи к следующему, пока не раскрыл текущий в 2-3 сценах.

2. НАЗЫВАТЬ БРЕНДЫ РАЗРЕШЕНО И ОБЯЗАТЕЛЬНО.
   Примеры: ChatGPT, Claude, Gemini, Midjourney, Perplexity, Runway,
   Synthesia, ElevenLabs, Notion AI, Copy.ai, Jasper, Leonardo AI.
   НЕ пиши «один из инструментов» — пиши имена.

3. КАЖДАЯ СЦЕНА ПРО ИНСТРУМЕНТ НАЧИНАЕТСЯ С ЕГО ИМЕНИ.
   Пример: «Первое место — ChatGPT. Это чат-бот от OpenAI...»

4. СТРУКТУРА:
   - Сцена 1-2: КРЮЧОК — удивительный факт с цифрой.
   - Сцена 3: ПРОБЛЕМА — почему это важно.
   - Далее: по 2-3 сцены на КАЖДЫЙ инструмент (ЧТО → ФУНКЦИИ → ЦЕНА → ПРИМЕР → МИНУС).
   - Сцена-практика: что делать прямо сегодня.
   - Финал: призыв подписаться.

5. КОНКРЕТИКА:
   - Плохо: «это удобно» — Хорошо: «экономит 3 часа в неделю»
   - Плохо: «много функций» — Хорошо: «пишет код, переводит, генерирует идеи»
   - Плохо: «доступная цена» — Хорошо: «бесплатно до 10 запросов, потом 20$/мес»

6. ЗАПРЕЩЕНЫ ФРАЗЫ:
   «сегодня мы поговорим», «в современном мире», «многие эксперты считают»,
   «не секрет, что», «стоит отметить», «это очень важно».

7. КАЖДАЯ СЦЕНА — 8-10 ПРЕДЛОЖЕНИЙ.
8. НИКАКОГО MARKDOWN (без **, ##, ---, ```).

ФОРМАТ ОТВЕТА (строго):

[SCENE 1]
GROUP: intro
VISUAL: 3-5 english words describing a concrete visual subject
TEXT: Текст сцены, 8-10 предложений.

[SCENE 2]
GROUP: intro
VISUAL: ...
TEXT: ...

[SCENE 3]
GROUP: ChatGPT
VISUAL: person typing laptop chat
TEXT: Первое место — ChatGPT. Это...

... и так далее.

ПРАВИЛА GROUP:
1. GROUP — имя инструмента (ChatGPT, Claude, Midjourney) или intro/outro.
2. Все сцены про ОДИН инструмент идут ПОДРЯД и имеют ОДИН GROUP.

ПРАВИЛА VISUAL:
1. На английском, 3-5 слов.
2. КОНКРЕТНЫЙ визуальный объект из TEXT этой сцены.
3. НЕ используй абстракции: technology, business, future, concept.
4. НЕ используй бренды в VISUAL — только общий образ.

ВЕРНИ ТОЛЬКО СЦЕНЫ. 15-25 штук. Без пояснений."""

        script = self._generate(prompt)
        if script:
            print(f"✅ Сценарий сгенерирован ({len(script)} символов)")
            return script
        print("❌ Не удалось сгенерировать сценарий, использую fallback")
        return self._fallback_script(topic, niche)

    def _fallback_script(self, topic, niche):
        return f"""[SCENE 1]
GROUP: intro
VISUAL: person typing laptop
TEXT: Привет! Сегодня разберём {topic}. Ты узнаешь конкретные инструменты с ценами, примерами и минусами.

[SCENE 2]
GROUP: intro
VISUAL: data charts screen
TEXT: 70% людей теряют время на рутину, которую можно автоматизировать. Разберём конкретные решения.

[SCENE 3]
GROUP: ChatGPT
VISUAL: person typing laptop chat
TEXT: Первое место — ChatGPT от OpenAI. Чат-бот на базе GPT-4, выпущен в 2022 году. Умеет писать тексты, отвечать на вопросы, генерировать код. Бесплатная версия с лимитами, Plus за 20$ в месяц. Кейс: копирайтер Сергей сократил время на статьи в 3 раза. Минус: иногда выдаёт устаревшие данные.

[SCENE 4]
GROUP: Midjourney
VISUAL: digital art painting colorful
TEXT: Второе место — Midjourney. Генерирует изображения по тексту за 30 секунд. Стоит от 10$ в месяц. Дизайнер Ольга делает обложки за 5 минут вместо 2 часов. Минус: нужен навык промптов.

[SCENE 5]
GROUP: outro
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

        prompt = f"""На основе сценария создай метаданные для YouTube.

НИША: {niche}
СЦЕНАРИЙ (фрагмент): {script[:1500]}

ФОРМАТ ОТВЕТА (строго):

НАЗВАНИЕ: цепляющее название до 60 символов, с цифрой
ОПИСАНИЕ: описание 100-200 слов с ключевыми словами
ТЕГИ: тег1, тег2, тег3, ... (10 штук)"""

        result = self._generate(prompt)
        if result:
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

        return {
            "title": f"{niche}: обзор",
            "description": script[:200],
            "tags": [niche, "youtube", "автоматизация"],
        }
