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

        prompt = f"""Напиши сценарий Shorts (50 секунд, 8-12 предложений).

ТЕМА: {topic}
ФАКТЫ: {research[:800]}

СТРУКТУРА РАССКАЗА:
1. Крючок — противоречие.
2. Проблема — что теряет человек.
3. Решение 1 через ChatGPT.
4. Решение 2 через Notion AI.
5. Решение 3 через Midjourney.
6. Вывод — что делать.
7. Цикл-крючок в конце.

ЖЁСТКИЕ ПРАВИЛА:
1. КАЖДАЯ сцена = РОВНО ОДНО предложение.
2. КАЖДАЯ сцена имеет СВОЙ VISUAL — 5-10 слов, детальное описание кадра.
3. VISUAL описывает КОНКРЕТНУЮ СЦЕНУ: кто, что делает, где.
4. Всего 8-12 сцен.
5. Запрещены: «сегодня мы поговорим», «в современном мире», «многие эксперты».

ФОРМАТ (строго):

[SCENE 1]
GROUP: intro
VISUAL: close up of frustrated writer at desk, crumpled papers, dim lighting
TEXT: Твои тексты не работают не потому, что ты плохо пишешь.

[SCENE 2]
GROUP: intro
VISUAL: close up of hands typing on laptop keyboard, chat window on screen
TEXT: А потому что ты делаешь их вручную.

[SCENE 3]
GROUP: ChatGPT
VISUAL: person typing on laptop, ChatGPT interface on screen, office desk
TEXT: ChatGPT пишет черновик за 10 минут.

[SCENE 4]
GROUP: ChatGPT
VISUAL: close up of timer on phone screen, countdown showing 10 minutes
TEXT: НО он не помнит твои задачи.

... и так далее, 8-12 сцен.

ПРАВИЛА VISUAL:
1. На английском, 5-10 слов.
2. КОНКРЕТНАЯ СЦЕНА: человек + действие + детали.
3. ХОРОШИЕ: "close up of man hands typing on laptop keyboard, office desk, coffee cup".
4. ЗАПРЕЩЕНЫ: "fast data flow", "multimodal workspace", "digital transformation".
5. Каждый VISUAL — УНИКАЛЬНЫЙ.

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
VISUAL: close up of frustrated writer at desk, crumpled papers, dim lighting
TEXT: Твои тексты не работают не потому, что ты плохо пишешь.

[SCENE 2]
GROUP: intro
VISUAL: close up of hands typing on laptop keyboard, chat window on screen
TEXT: А потому что ты делаешь их вручную.

[SCENE 3]
GROUP: ChatGPT
VISUAL: person typing on laptop, ChatGPT interface on screen, office desk
TEXT: ChatGPT пишет черновик за 10 минут.

[SCENE 4]
GROUP: ChatGPT
VISUAL: close up of timer on phone screen, countdown showing 10 minutes
TEXT: НО он не помнит твои задачи.

[SCENE 5]
GROUP: Notion AI
VISUAL: person writing notes in organizer on wooden desk, warm sunlight
TEXT: ПОЭТОМУ нужен Notion AI — он ведёт заметки.

[SCENE 6]
GROUP: Notion AI
VISUAL: close up of notebook with organized list, pencil, coffee cup
TEXT: Стоит 10$ в месяц.

[SCENE 7]
GROUP: Midjourney
VISUAL: designer drawing on tablet with stylus, colorful digital art on screen
TEXT: А для обложек — Midjourney.

[SCENE 8]
GROUP: Midjourney
VISUAL: close up of digital art on monitor, bright colors, creative studio
TEXT: Делает картинку за 5 минут, от 10$ в месяц.

[SCENE 9]
GROUP: outro
VISUAL: person looking at phone with surprised expression, bright background
TEXT: Ты всё ещё тратишь 4 часа в день?

[SCENE 10]
GROUP: outro
VISUAL: subscribe button animation, red bell icon, bright yellow background
TEXT: Тогда следующий шаг — вот он.
"""
