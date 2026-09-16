import os
import re
import time
from openai import OpenAI

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"

MAX_ATTEMPTS = 2
MIN_SCORE = 7
PAUSE = 20


class ScriptGenerator:
    def __init__(self):
        self.client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        self.last_score = 0

    def _ask(self, role, prompt, temperature=0.7, retries=3):
        for attempt in range(retries):
            try:
                r = self.client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": role},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=temperature,
                    max_tokens=3000,
                )
                return r.choices[0].message.content
            except Exception as e:
                if "429" in str(e):
                    time.sleep(15 * (attempt + 1))
                    continue
                return None
        return None

    def pick_best_topic(self, niche, recent_topics=None, best_topics=None):
        print(f"\n🧠 Выбираю тему: {niche}")
        recent_topics = recent_topics or []

        role = "Ты — стратег YouTube Shorts."
        prompt = f"""Выбери тему для Shorts (30-45 секунд).

НИША: {niche}
УЖЕ ДЕЛАЛИ: {", ".join(recent_topics[-10:]) if recent_topics else "ничего"}

Тема должна быть про КОНКРЕТНУЮ проблему, не «AI вообще».

ПРИМЕРЫ ХОРОШИХ ТЕМ:
- Почему твои тексты не работают (и как ChatGPT это исправит)
- 3 ошибки в ChatGPT, которые убивают результат
- Я неделю делал всё через AI. Вот что сломалось

ЗАДАЧА: придумай 5 тем, выбери 1.

ФОРМАТ:
ТЕМЫ:
1. <тема>
2. <тема>
3. <тема>
4. <тема>
5. <тема>

ЛУЧШАЯ: <номер>"""

        result = self._ask(role, prompt, temperature=0.8)
        topics = re.findall(r"^\d+\.\s*(.+)$", result or "", re.MULTILINE)
        m = re.search(r"ЛУЧШАЯ:\s*(\d+)", result or "")
        n = int(m.group(1)) if m else 1
        chosen = topics[n-1].strip() if topics and 1 <= n <= len(topics) else (topics[0].strip() if topics else "Почему твои тексты не работают")
        print(f"   ✅ Тема: {chosen}")
        return chosen

    def _research(self, topic, niche):
        print("   🔍 Ресёрчер...")
        role = "Ты — исследователь. Только РЕАЛЬНЫЕ продукты."
        prompt = f"""Собери 3 факта про РЕАЛЬНЫЕ AI-инструменты.

ТЕМА: {topic}

РАЗРЕШЁННЫЕ: ChatGPT, Claude, Midjourney, Notion AI, Perplexity, Gemini.

Для 3 инструментов:
- Название
- Цена (бесплатно / от X$)
- 1 цифра (пользователи, экономия времени)

Максимум 800 символов."""
        return self._ask(role, prompt, temperature=0.3) or ""

    def _write_shorts(self, topic, niche, research, feedback=""):
        print("   ✍️ Сценарист...")
        role = "Ты — сценарист YouTube Shorts. Пишешь по канонам удержания."

        prompt = f"""Напиши сценарий Shorts (30-45 секунд, ~100 слов).

ТЕМА: {topic}
ФАКТЫ: {research[:800]}

СТРУКТУРА (обязательно):

**0-3 сек — КРЮЧОК**
Не «знаете, что». Сразу боль или противоречие.
Формула: «[Название проблемы] — не потому что [ожидание]. А потому что [реальность]»
Пример: «Твои тексты не работают не потому, что ты плохо пишешь. А потому что ты пишешь их вручную»

**3-8 сек — СТАВКИ**
Почему это важно. Что теряет человек.
Пример: «Это съедает 4 часа в день. Каждый день.»

**8-30 сек — ЦЕННОСТЬ через «НО» и «ПОЭТОМУ»**
Инструмент 1 → НО проблема → ПОЭТОМУ инструмент 2 → А для X → инструмент 3.
Пример: «ChatGPT пишет черновик за 10 минут. НО он не помнит твои задачи. ПОЭТОМУ нужен Notion AI. А для обложек — Midjourney.»

**30-40 сек — ВЫВОД + ЦИКЛ**
Последняя фраза должна цеплять крючок.
Пример: «Ты всё ещё тратишь 4 часа? Тогда вот следующий шаг» (и видео начинается заново)

ЗАПРЕЩЕНО:
- «Сегодня мы поговорим», «в современном мире», «многие эксперты»
- «И ещё есть...» — только «НО» и «ПОЭТОМУ»
- Длинные предложения (>15 слов)

ФОРМАТ:

[SCENE 1]
GROUP: intro
VISUAL: 3-5 english words
TEXT: Крючок (1 предложение).

[SCENE 2]
GROUP: <инструмент 1>
VISUAL: 3-5 english words
TEXT: 1-2 предложения.

[SCENE 3]
GROUP: <инструмент 2>
VISUAL: 3-5 english words
TEXT: 1-2 предложения.

[SCENE 4]
GROUP: <инструмент 3>
VISUAL: 3-5 english words
TEXT: 1-2 предложения + вывод.

[SCENE 5]
GROUP: outro
VISUAL: subscribe button
TEXT: Цикл-крючок (1 предложение).

ВЕРНИ ТОЛЬКО СЦЕНЫ."""

        if feedback:
            prompt += f"\n\nИСПРАВЬ:\n{feedback[:300]}"

        return self._ask(role, prompt) or ""

    def _critic_shorts(self, script):
        print("   🧐 Критик...")
        role = "Ты — строгий редактор Shorts."

        prompt = f"""Оцени по 4 критериям (каждый 1-10):

СЦЕНАРИЙ:
{script[:2000]}

1. КРЮЧОК: первые 3 сек — боль/противоречие? (не «знаете, что»)
2. СВЯЗКИ: есть «НО» и «ПОЭТОМУ»? (не «и ещё»)
3. ЦИКЛ: последняя фраза цепляет начало?
4. ПЛОТНОСТЬ: нет воды, каждое слово работает?

ФОРМАТ:
ОЦЕНКА: <среднее>
ВЕРДИКТ: <PASS/FAIL>
ФИДБЕК: <1 предложение>"""

        result = self._ask(role, prompt, temperature=0.2)
        score, verdict, feedback = 5, "FAIL", ""
        for line in (result or "").split("\n"):
            if line.startswith("ОЦЕНКА:"):
                try: score = int(line.replace("ОЦЕНКА:", "").strip().split()[0])
                except: pass
            elif line.startswith("ВЕРДИКТ:"):
                verdict = line.replace("ВЕРДИКТ:", "").strip()
            elif line.startswith("ФИДБЕК:"):
                feedback = line.replace("ФИДБЕК:", "").strip()
        return score, verdict, feedback

    def generate_shorts_script(self, topic, niche):
        print(f"\n📝 Сценарий: {topic}")
        if not self.client:
            return self._fallback_script(topic, niche)

        research = self._research(topic, niche)
        best_script, best_score, feedback = None, 0, ""

        for attempt in range(1, MAX_ATTEMPTS + 1):
            print(f"\n   --- Итерация {attempt}/{MAX_ATTEMPTS} ---")
            if attempt > 1:
                time.sleep(PAUSE)
            script = self._write_shorts(topic, niche, research, feedback)
            if not script:
                continue
            score, verdict, feedback = self._critic_shorts(script)
            print(f"   Оценка: {score}/10 ({verdict})")
            if score > best_score:
                best_score, best_script = score, script
            if score >= MIN_SCORE:
                print(f"✅ Принят")
                break
            print(f"⚠️ Переделка...")

        self.last_score = best_score
        return best_script or self._fallback_script(topic, niche)

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
VISUAL: stressed writer deadline
TEXT: Твои тексты не работают не потому, что ты плохо пишешь. А потому что ты делаешь это вручную.

[SCENE 2]
GROUP: ChatGPT
VISUAL: person typing laptop chat
TEXT: ChatGPT пишет черновик за 10 минут. НО он не помнит твои задачи.

[SCENE 3]
GROUP: Notion AI
VISUAL: notebook organizer screen
TEXT: ПОЭТОМУ нужен Notion AI — он ведёт заметки и планирует день. Стоит 10$ в месяц.

[SCENE 4]
GROUP: Midjourney
VISUAL: digital art painting colorful
TEXT: А для обложек — Midjourney. Делает картинку за 5 минут, от 10$ в месяц. Вот почему 70% фрилансеров уже используют AI.

[SCENE 5]
GROUP: outro
VISUAL: subscribe button animation
TEXT: Ты всё ещё тратишь 4 часа? Тогда следующий шаг — вот он.
"""
