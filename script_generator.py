import os
import re
from openai import OpenAI

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"

MAX_ATTEMPTS = 3
MIN_SCORE = 7
MAX_PROMPT_CHARS = 5000


class ScriptGenerator:
    def __init__(self):
        self.client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        if not self.client:
            print("⚠️  GROQ_API_KEY не задан.")
        self.last_score = 0

    def _truncate(self, text, max_chars=MAX_PROMPT_CHARS):
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n[...обрезано...]"

    def _ask(self, role, prompt, temperature=0.7):
        try:
            r = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": role},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=4000,
            )
            return r.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Groq: {str(e)[:150]}")
            return None

    # ============ АВТОВЫБОР ТЕМЫ ============
    def pick_best_topic(self, niche, recent_topics=None, best_topics=None):
        print(f"\n🧠 Агент выбирает тему: {niche}")
        recent_topics = recent_topics or []
        best_topics = best_topics or []

        role = "Ты — стратег YouTube Shorts."
        prompt = f"""Выбери ЛУЧШУЮ тему для Shorts (60 секунд).

НИША: {niche}
УЖЕ ДЕЛАЛИ: {", ".join(recent_topics[-10:]) if recent_topics else "ничего"}

ЗАДАЧА: придумай 5 тем с ЧИСЛОМ (Топ-3, 5 ошибок), выбери 1 лучшую.

ФОРМАТ:
ТЕМЫ:
1. <тема>
2. <тема>
3. <тема>
4. <тема>
5. <тема>

ЛУЧШАЯ: <номер>"""

        result = self._ask(role, prompt, temperature=0.8)
        if not result:
            return "Топ-3 AI инструмента для работы"

        topics = re.findall(r"^\d+\.\s*(.+)$", result, re.MULTILINE)
        m = re.search(r"ЛУЧШАЯ:\s*(\d+)", result)
        n = int(m.group(1)) if m else 1
        chosen = topics[n - 1].strip() if topics and 1 <= n <= len(topics) else (topics[0].strip() if topics else "Топ-3 AI инструмента")
        print(f"   ✅ Тема: {chosen}")
        return chosen

    # ============ РЕСЁРЧЕР ============
    def _research(self, topic, niche):
        print("   🔍 Ресёрчер ищет факты...")
        role = "Ты — исследователь технологий."
        prompt = f"""Собери факты про РЕАЛЬНО СУЩЕСТВУЮЩИЕ AI-инструменты.

НИША: {niche}
ТЕМА: {topic}

ВАЖНО: используй ТОЛЬКО реальные инструменты, которые есть на рынке:
ChatGPT, Claude, Gemini, Midjourney, Perplexity, Runway, Synthesia,
ElevenLabs, Notion AI, Copy.ai, Jasper, Leonardo AI, Suno, HeyGen.

НЕ ПРИДУМЫВАЙ новые названия! Если не знаешь точного — не пиши.

Верни:
1. 3-5 РЕАЛЬНЫХ инструментов с названиями
2. Для каждого: цена (бесплатно / от X$/мес)
3. 1-2 цифры (пользователи, экономия времени)
4. 1 минус у каждого

Максимум 2000 символов."""
        return self._ask(role, prompt, temperature=0.3) or ""

    # ============ СЦЕНАРИСТ SHORTS ============
    def _write_shorts(self, topic, niche, research, feedback=""):
        print("   ✍️ Сценарист пишет...")
        role = "Ты — сценарист YouTube Shorts. Очень коротко и цепляюще."
        research_short = self._truncate(research, 1500)

        prompt = f"""Создай сценарий для YouTube Shorts (60-80 секунд).

НИША: {niche}
ТЕМА: {topic}

ИССЛЕДОВАНИЕ:
{research_short}

ЖЁСТКИЕ ПРАВИЛА:
1. РОВНО 5 сцен: 1 крючок + 3 инструмента + 1 финал.
2. В КАЖДОЙ сцене — РОВНО 2-3 предложения. Не больше 3! Не меньше 2!
3. Только РЕАЛЬНЫЕ инструменты из исследования.
4. НЕ ПРИДУМЫВАЙ новые названия инструментов!
5. В каждой сцене про инструмент — ЕГО ИМЯ, ЦЕНА, ПРИМЕР.
6. ЗАПРЕЩЕНЫ фразы: «сегодня мы поговорим», «в современном мире», «многие эксперты», «стоит отметить», «не секрет, что», «как вы знаете», «важно понимать».
7. Первое предложение первой сцены — СРАЗУ цифра или вопрос (крючок).

ФОРМАТ (строго):

[SCENE 1]
GROUP: intro
VISUAL: 3-5 english words
TEXT: Два предложения с цифрой или вопросом.

[SCENE 2]
GROUP: <название инструмента>
VISUAL: 3-5 english words
TEXT: Два-три предложения. Имя инструмента — в начале.

[SCENE 3]
GROUP: <название инструмента>
VISUAL: ...
TEXT: Два-три предложения.

[SCENE 4]
GROUP: <название инструмента>
VISUAL: ...
TEXT: Два-три предложения.

[SCENE 5]
GROUP: outro
VISUAL: subscribe button
TEXT: Одно предложение — призыв подписаться.

ВЕРНИ ТОЛЬКО СЦЕНЫ."""

        if feedback:
            prompt += f"\n\nФИДБЕК (исправь):\n{self._truncate(feedback, 400)}"

        return self._ask(role, prompt) or ""

    # ============ КРИТИК SHORTS ============
    def _critic_shorts(self, script):
        print("   🧐 Критик проверяет...")
        role = "Ты — строгий редактор YouTube Shorts."
        script_short = self._truncate(script, 3000)

        prompt = f"""Оцени сценарий Shorts (каждый критерий 1-10).

СЦЕНАРИЙ:
{script_short}

КРИТЕРИИ:
1. КОРОТКОСТЬ: каждая сцена РОВНО 2-3 предложения?
   (2-3 предложения — это ХОРОШО, ставь 9-10. НЕ требуй больше.)
2. КОНКРЕТИКА: есть названия РЕАЛЬНЫХ инструментов, цены, цифры?
3. НЕТ ВОДЫ: нет «сегодня мы поговорим», «в современном мире»?
4. СЦЕН РОВНО 5?
5. КРЮЧОК: первая сцена сразу цепляет цифрой или вопросом?

ВАЖНО: короткий текст — это НЕ минус, а плюс для Shorts.

ФОРМАТ:
ОЦЕНКА: <среднее 1-10>
ВЕРДИКТ: <PASS если >= 7, FAIL если < 7>
ФИДБЕК: <2 предложения>"""

        result = self._ask(role, prompt, temperature=0.3) or ""
        score, verdict, feedback = 5, "FAIL", ""
        for line in result.split("\n"):
            if line.startswith("ОЦЕНКА:"):
                try:
                    score = int(line.replace("ОЦЕНКА:", "").strip().split()[0])
                except Exception:
                    pass
            elif line.startswith("ВЕРДИКТ:"):
                verdict = line.replace("ВЕРДИКТ:", "").strip()
            elif line.startswith("ФИДБЕК:"):
                feedback = line.replace("ФИДБЕК:", "").strip()
        return score, verdict, feedback

    # ============ ГЛАВНЫЙ ЦИКЛ ============
    def generate_shorts_script(self, topic, niche):
        print(f"\n📝 Генерирую сценарий: {topic}")
        if not self.client:
            return self._fallback_script(topic, niche)

        research = self._research(topic, niche)
        if research:
            print(f"   ✅ Ресёрч ({len(research)} символов)")

        best_script = None
        best_score = 0
        feedback = ""

        for attempt in range(1, MAX_ATTEMPTS + 1):
            print(f"\n   --- Итерация {attempt}/{MAX_ATTEMPTS} ---")
            script = self._write_shorts(topic, niche, research, feedback)
            if not script:
                continue
            score, verdict, feedback = self._critic_shorts(script)
            print(f"   Оценка: {score}/10 ({verdict})")
            if score > best_score:
                best_score = score
                best_script = script
            if score >= MIN_SCORE:
                print(f"✅ Принят (оценка {score})")
                break
            print(f"⚠️ Переделка...")

        self.last_score = best_score
        if not best_script:
            return self._fallback_script(topic, niche)

        print(f"✅ Итог: {best_score}/10, {len(best_script)} символов")
        return best_script

    def extract_tools(self, script):
        tools = set()
        for m in re.finditer(r"GROUP:\s*(.+)", script):
            g = m.group(1).strip()
            if g.lower() not in ("intro", "outro") and len(g) < 30:
                tools.add(g)
        return sorted(tools)

    def generate_title_and_description(self, script, niche):
        print("\n🎬 SEO-мастер делает метаданные...")
        if not self.client:
            return {"title": f"{niche}", "description": script[:200], "tags": [niche]}

        role = "Ты — SEO-специалист YouTube Shorts."
        prompt = f"""Создай метаданные для Shorts.

НИША: {niche}
СЦЕНАРИЙ: {self._truncate(script, 2000)}

ФОРМАТ:
НАЗВАНИЕ: до 50 символов, с цифрой
ОПИСАНИЕ: 50-100 слов
ТЕГИ: 8 тегов через запятую"""

        result = self._ask(role, prompt) or ""
        title, description, tags = "", "", []
        for line in result.split("\n"):
            if line.startswith("НАЗВАНИЕ:"):
                title = line.replace("НАЗВАНИЕ:", "").strip()
            elif line.startswith("ОПИСАНИЕ:"):
                description = line.replace("ОПИСАНИЕ:", "").strip()
            elif line.startswith("ТЕГИ:"):
                tags = [t.strip() for t in line.replace("ТЕГИ:", "").split(",") if t.strip()]

        print(f"✅ Название: {title or niche}")
        return {"title": title or f"{niche}", "description": description or script[:200], "tags": tags or [niche]}

    def _fallback_script(self, topic, niche):
        return f"""[SCENE 1]
GROUP: intro
VISUAL: fast numbers countdown
TEXT: 70% людей теряют 3 часа в день на рутину. Вот 3 AI, которые это исправят.

[SCENE 2]
GROUP: ChatGPT
VISUAL: person typing laptop chat
TEXT: ChatGPT от OpenAI — бесплатно, Plus за 20$ в месяц. Пишет тексты и код в 3 раза быстрее.

[SCENE 3]
GROUP: Midjourney
VISUAL: digital art painting colorful
TEXT: Midjourney делает обложку за 5 минут, от 10$ в месяц. Дизайнеры экономят 2 часа на каждой.

[SCENE 4]
GROUP: Notion AI
VISUAL: notebook organizer screen
TEXT: Notion AI ведёт заметки и планирует день. 10$ в месяц — экономит час в день.

[SCENE 5]
GROUP: outro
VISUAL: subscribe button animation
TEXT: Подписывайся — дальше больше AI-лайфхаков.
"""
