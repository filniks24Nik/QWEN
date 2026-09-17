import os
import re
import time
from openai import OpenAI

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"


class ScriptGenerator:
    def __init__(self):
        self.client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        self.last_score = 8

    def _ask(self, role, prompt, temperature=0.7, retries=2):
        for attempt in range(retries):
            try:
                r = self.client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": role},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=temperature,
                    max_tokens=2000,
                )
                return r.choices[0].message.content
            except Exception as e:
                if "429" in str(e):
                    time.sleep(20)
                    continue
                print(f"⚠️ Groq: {str(e)[:120]}")
                return None
        return None

    def pick_best_topic(self, niche, recent_topics=None, best_topics=None):
        print(f"\n🧠 Выбираю тему: {niche}")
        recent_topics = recent_topics or []

        role = "Ты — стратег YouTube Shorts."
        prompt = f"""Выбери тему для Shorts (50 секунд).

НИША: {niche}
УЖЕ ДЕЛАЛИ: {", ".join(recent_topics[-10:]) if recent_topics else "ничего"}

ВАЖНО: тема — про КОНКРЕТНУЮ проблему. НЕ пиши год (2026, 2027).

ПРИМЕРЫ ХОРОШИХ ТЕМ:
- Почему твои тексты не работают
- 3 AI-инструмента, которые заменят копирайтера
- Я неделю работал только через AI. Вот что сломалось

ЗАДАЧА: придумай 5 тем, выбери 1.

ФОРМАТ:
ТЕМЫ:
1. <тема>
2. <тема>
3. <тема>
4. <тема>
5. <тема>

ЛУЧШАЯ: <номер>"""

        result = self._ask(role, prompt, temperature=0.8) or ""
        topics = re.findall(r"^\d+\.\s*(.+)$", result, re.MULTILINE)
        m = re.search(r"ЛУЧШАЯ:\s*(\d+)", result)
        n = int(m.group(1)) if m else 1
        chosen = topics[n-1].strip() if topics and 1 <= n <= len(topics) else (topics[0].strip() if topics else "Почему твои тексты не работают")
        print(f"   ✅ Тема: {chosen}")
        return chosen

    def _research(self, topic, niche):
        print("   🔍 Ресёрчер...")
        role = "Ты — исследователь. Только РЕАЛЬНЫЕ продукты."
        prompt = f"""Собери 3 факта про РЕАЛЬНЫЕ AI-инструменты.

ТЕМА: {topic}

РАЗРЕШЁННЫЕ: ChatGPT, Claude, Gemini, Midjourney, Notion AI, Perplexity.

Для 3 инструментов:
- Название
- Цена
- 1 цифра (пользователи, экономия времени)

Максимум 600 символов."""
        return self._ask(role, prompt, temperature=0.3) or ""

    def _write_shorts(self, topic, niche, research):
        print("   ✍️ Сценарист...")
        role = "Ты — сценарист YouTube Shorts. Пишешь по канонам удержания."

        prompt = f"""Напиши сценарий Shorts (50 секунд, ~80 слов).

ТЕМА: {topic}
ФАКТЫ: {research[:800]}

СТРУКТУРА:

**0-3 сек — КРЮЧОК**
Не «знаете, что». Сразу противоречие.
Формула: «[Проблема] не потому что [ожидание]. А потому что [реальность]»
Пример: «Твои тексты не работают не потому, что ты плохо пишешь. А потому что ты пишешь их вручную»

**3-8 сек — СТАВКИ**
Что теряет человек. Одна цифра.

**8-45 сек — ЦЕННОСТЬ через «НО» и «ПОЭТОМУ»**
Инструмент 1 → НО проблема → ПОЭТОМУ инструмент 2 → А для X → инструмент 3.
Пример: «ChatGPT пишет черновик за 10 минут. НО он не помнит твои задачи. ПОЭТОМУ нужен Notion AI. А для обложек — Midjourney.»

**45-50 сек — ВЫВОД + ЦИКЛ**
Последняя фраза цепляет крючок.
Пример: «Ты всё ещё тратишь 4 часа? Тогда вот следующий шаг.»

ЗАПРЕЩЕНО:
- «Сегодня мы поговорим», «в современном мире», «многие эксперты»
- «И ещё есть...» — только «НО» и «ПОЭТОМУ»
- Предложения длиннее 15 слов
- Год 2026 в тексте

ФОРМАТ:

[SCENE 1]
GROUP: intro
VISUAL: 5-10 english words, detailed scene description
TEXT: Крючок (1-2 предложения).

[SCENE 2]
GROUP: <инструмент 1>
VISUAL: 5-10 english words, detailed scene description
TEXT: 1-2 предложения.

[SCENE 3]
GROUP: <инструмент 2>
VISUAL: 5-10 english words, detailed scene description
TEXT: 1-2 предложения.

[SCENE 4]
GROUP: <инструмент 3>
VISUAL: 5-10 english words, detailed scene description
TEXT: 1-2 предложения + вывод.

[SCENE 5]
GROUP: outro
VISUAL: subscribe button animation
TEXT: Цикл-крючок (1 предложение).

ПРАВИЛА ДЛЯ VISUAL (для AI-генерации картинок):
1. VISUAL — на английском, 5-10 слов, ДЕТАЛЬНОЕ описание сцены.
2. Описывай ЧТО В КАДРЕ: кто, что делает, где, какие детали.
3. ПРИМЕРЫ ХОРОШИХ VISUAL:
   - "close up of man hands typing on laptop keyboard, office desk, coffee cup"
   - "young woman writing in notebook at wooden desk, warm sunlight"
   - "person holding smartphone looking at screen, blurred city background"
   - "hands of designer drawing on tablet with stylus, creative studio"
4. НЕ используй абстракции: "fast data flow", "digital transformation".
5. НЕ используй названия брендов (ChatGPT → "person typing").
6. Представь, что описываешь кадр для фотографа.

ВЕРНИ ТОЛЬКО СЦЕНЫ."""

        return self._ask(role, prompt) or ""

    def generate_shorts_script(self, topic, niche):
        print(f"\n📝 Сценарий: {topic}")
        if not self.client:
            return self._fallback_script(topic, niche)

        research = self._research(topic, niche)
        script = self._write_shorts(topic, niche, research)
        if script:
            print(f"✅ Сценарий ({len(script)} символов)")
            return script
        return self._fallback_script(topic, niche)

    def extract_tools(self, script):
        tools = set()
        for m in re.finditer(r"GROUP:\s*(.+)", script):
            g = m.group(1).strip()
            if g.lower() not in ("intro", "outro") and len(g) < 30:
                tools.add(g)
        return sorted(tools)

    def generate_title_and_description(self, script, niche):
        print("\n🎬 SEO...")
        if not self.client:
            return {"title": niche, "description": script[:200], "tags": [niche]}
        role = "Ты — SEO-специалист."
        prompt = f"""Создай метаданные Shorts.

НИША: {niche}
СЦЕНАРИЙ: {script[:1500]}

ФОРМАТ:
НАЗВАНИЕ: до 50 символов
ОПИСАНИЕ: 50-100 слов
ТЕГИ: 8 тегов"""
        result = self._ask(role, prompt) or ""
        title, desc, tags = "", "", []
        for line in result.split("\n"):
            if line.startswith("НАЗВАНИЕ:"): title = line.replace("НАЗВАНИЕ:", "").strip()
            elif line.startswith("ОПИСАНИЕ:"): desc = line.replace("ОПИСАНИЕ:", "").strip()
            elif line.startswith("ТЕГИ:"): tags = [t.strip() for t in line.replace("ТЕГИ:", "").split(",") if t.strip()]
        return {"title": title or niche, "description": desc or script[:200], "tags": tags or [niche]}

    def _fallback_script(self, topic, niche):
        return f"""[SCENE 1]
GROUP: intro
VISUAL: close up of stressed writer at desk, crumpled papers, dim lighting
TEXT: Твои тексты не работают не потому, что ты плохо пишешь. А потому что ты делаешь это вручную.

[SCENE 2]
GROUP: ChatGPT
VISUAL: close up of hands typing on laptop keyboard, chat window on screen, office desk
TEXT: ChatGPT пишет черновик за 10 минут. НО он не помнит твои задачи.

[SCENE 3]
GROUP: Notion AI
VISUAL: person writing notes in organizer on wooden desk, warm sunlight, coffee cup
TEXT: ПОЭТОМУ нужен Notion AI — он ведёт заметки. Стоит 10$ в месяц.

[SCENE 4]
GROUP: Midjourney
VISUAL: designer drawing on tablet with stylus, colorful digital art on screen, creative studio
TEXT: А для обложек — Midjourney. Делает картинку за 5 минут, от 10$ в месяц.

[SCENE 5]
GROUP: outro
VISUAL: subscribe button animation, red bell icon, bright yellow background
TEXT: Ты всё ещё тратишь 4 часа? Тогда следующий шаг — вот он.
"""
