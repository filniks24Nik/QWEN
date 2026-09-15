from google import genai
from config import GEMINI_API_KEY

# Основная — pro для глубины. Fallback — flash, если pro недоступна/лимит.
MODEL_PRIMARY = "gemini-3.1-pro-preview"
MODEL_FALLBACK = "gemini-3.8-flash"


class ScriptGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
        if not self.client:
            print("⚠️  GEMINI_API_KEY не задан — буду использовать шаблонные тексты.")

    def _generate(self, prompt):
        """Пробует pro, при ошибке — flash. Возвращает текст или None."""
        for model in (MODEL_PRIMARY, MODEL_FALLBACK):
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                print(f"   (модель: {model})")
                return response.text
            except Exception as e:
                print(f"⚠️ {model} не сработала: {e}")
                continue
        return None

    def generate_script(self, topic, niche, duration_minutes=10):
        print(f"\n📝 Генерирую сценарий для: {topic}")

        if not self.client:
            return self._fallback_script(topic, niche)

        prompt = f"""
Ты — сценарист YouTube-канала про технологии. Создай КОНКРЕТНЫЙ сценарий.
Общие фразы ЗАПРЕЩЕНЫ. Только факты, названия, цифры, примеры.

НИША: {niche}
ТЕМА: {topic}
ДЛИТЕЛЬНОСТЬ: примерно {duration_minutes} минут

КРИТИЧЕСКИ ВАЖНО (читай внимательно):

1. ЕСЛИ В ТЕМЕ ЕСТЬ ЧИСЛО (Топ-5, 10 штук, 3 способа и т.п.):
   - Ты ОБЯЗАН назвать РОВНО столько конкретных инструментов/пунктов.
   - На КАЖДЫЙ инструмент — ОТДЕЛЬНЫЙ GROUP с его ИМЕНЕМ.
   - Название инструмента — ПЕРВОЕ СЛОВО первой сцены этой группы.
   - НЕ переходи к следующему, пока не раскрыл текущий в 2-3 сценах.
   - Не можешь назвать 5 — назови 3, но назови по именам. Абстракции запрещены.

2. НАЗЫВАТЬ БРЕНДЫ РАЗРЕШЕНО И ОБЯЗАТЕЛЬНО.
   Это не реклама. Это информация. Зритель ждёт конкретных названий.
   Примеры: ChatGPT, Claude, Gemini, Midjourney, Perplexity, Runway,
   Synthesia, ElevenLabs, Notion AI, Copy.ai, Jasper, Leonardo AI.
   НЕ пиши «один из инструментов», «некоторые сервисы» — пиши имена.

3. КАЖДАЯ СЦЕНА ПРО ИНСТРУМЕНТ НАЧИНАЕТСЯ С ЕГО ИМЕНИ.
   Пример: «Первое место — ChatGPT. Это чат-бот от OpenAI...»
   Пример: «На втором месте — Claude от Anthropic. Это...»

4. СТРУКТУРА:
   - Сцена 1-2: КРЮЧОК — удивительный факт с цифрой.
   - Сцена 3: ПРОБЛЕМА — почему это важно.
   - Далее: по 2-3 сцены на КАЖДЫЙ инструмент.
     Раскрывай по схеме: ЧТО → ФУНКЦИИ → ЦЕНА → ПРИМЕР → МИНУС.
   - Сцена-практика: что делать прямо сегодня.
   - Финал: призыв подписаться.

5. КОНКРЕТИКА (проверь каждое предложение):
   - Плохо: «это удобно» — Хорошо: «экономит 3 часа в неделю»
   - Плохо: «много функций» — Хорошо: «пишет код, переводит, генерирует идеи»
   - Плохо: «доступная цена» — Хорошо: «бесплатно до 10 запросов, потом 20$/мес»
   - Плохо: «популярный сервис» — Хорошо: «40 млн пользователей в 2024 году»

6. ЗАПРЕЩЕНЫ ФРАЗЫ (ни разу):
   - «сегодня мы поговорим»
   - «в современном мире»
   - «многие эксперты считают»
   - «не секрет, что»
   - «стоит отметить»
   - «это очень важно»

7. КАЖДАЯ СЦЕНА — 8-10 ПРЕДЛОЖЕНИЙ.
   Короткие сцены = поверхностное видео. Лучше меньше сцен, но глубже.

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

[SCENE 4]
GROUP: ChatGPT
VISUAL: chat interface screen
TEXT: ChatGPT умеет...

[SCENE 5]
GROUP: ChatGPT
VISUAL: writer office desk
TEXT: Цена и кому подходит...

[SCENE 6]
GROUP: Claude
VISUAL: person reading article
TEXT: Второе место — Claude от Anthropic. Это...

... и так далее.

ПРАВИЛА GROUP:
1. GROUP — имя инструмента (ChatGPT, Claude, Midjourney) или intro/outro.
2. Все сцены про ОДИН инструмент идут ПОДРЯД и имеют ОДИН GROUP.
3. НЕ используй общие GROUP типа «главное», «тема», «важное».

ПРАВИЛА VISUAL:
1. На английском, 3-5 слов.
2. КОНКРЕТНЫЙ визуальный объект из TEXT этой сцены.
3. Внутри одной группы VISUAL меняется, но остаётся в теме инструмента.
4. НЕ используй абстракции: technology, business, future, concept.
5. НЕ используй бренды в VISUAL — только общий образ
   (ChatGPT → «person typing», Midjourney → «digital art painting»).

ВЕРНИ ТОЛЬКО СЦЕНЫ. 15-25 штук. Без пояснений, без вступлений.
"""

        script = self._generate(prompt)
        if script:
            print(f"✅ Сценарий сгенерирован ({len(script)} символов)")
            return script
        print("❌ Не удалось сгенерировать сценарий")
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

        prompt = f"""
На основе сценария создай метаданные для YouTube.

НИША: {niche}
СЦЕНАРИЙ (фрагмент): {script[:1500]}

ФОРМАТ ОТВЕТА (строго):

НАЗВАНИЕ: цепляющее название до 60 символов, с цифрой
ОПИСАНИЕ: описание 100-200 слов с ключевыми словами
ТЕГИ: тег1, тег2, тег3, ... (10 штук)
"""

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
