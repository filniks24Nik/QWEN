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
            print("⚠️  GROQ_API_KEY не задан — буду использовать шаблонные тексты.")
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
        print(f"\n🧠 Агент выбирает тему для ниши: {niche}")
        recent_topics = recent_topics or []
        best_topics = best_topics or []

        role = "Ты — стратег YouTube Shorts. Выбираешь темы, которые залетают."
        prompt = f"""Выбери ЛУЧШУЮ тему для YouTube Shorts (60 секунд).

НИША: {niche}

УЖЕ ДЕЛАЛИ (не повторяйся):
{chr(10).join(f"- {t}" for t in recent_topics[-10:]) if recent_topics else "ничего ещё"}

ЗАДАЧА:
1. Придумай 5 РАЗНЫХ тем (не пересекайся).
2. Каждая тема — с ЧИСЛОМ (Топ-3, 5 ошибок).
3. Выбери 1 лучшую.

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
            return "Топ-3 AI для копирайтеров"

        topics = re.findall(r"^\d+\.\s*(.+)$", result, re.MULTILINE)
        m = re.search(r"ЛУЧШАЯ:\s*(\d+)", result)
        n = int(m.group(1)) if m else 1
        chosen = topics[n - 1].strip() if topics and 1 <= n <= len(topics) else (topics[0].strip() if topics else "Топ-3 AI для копирайтеров")
        print(f"   ✅ Выбрана тема: {chosen}")
        return chosen

    # ============ РЕСЁРЧЕР ============
    def _research(self, topic, niche):
        print("   🔍 Ресёрчер ищет факты...")
        role = "Ты — исследователь. Собираешь конкретные факты."
        prompt = f"""Собери 4-6 конкретных фактов по теме для Shorts.

НИША: {niche}
ТЕМА: {topic}

Верни:
1. 4-6 инструментов/фактов с названиями
2. Цены (если есть)
3. 1-2 цифры

Только факты. Без воды. Максимум 2000 символов."""
        return self._ask(role, prompt, temperature=0.4) or ""

    # ============ СЦЕНАРИСТ SHORTS ============
    def _write_shorts(self, topic, niche, research, feedback=""):
        print("   ✍️ Сценарист пишет короткий сценарий...")
        role = "Ты — сценарист YouTube Shorts. Пишешь очень коротко и цепляюще."
        research_short = self._truncate(research, 1500)

        prompt = f"""Создай сценарий для YouTube Shorts (60 секунд, 4-6 сцен).

НИША: {niche}
ТЕМА: {topic}

ИССЛЕДОВАНИЕ:
{research_short}

ЖЁСТКИЕ ПРАВИЛА:
1. РОВНО 4-6 сцен. Не больше, не меньше.
2. Каждая сцена — РОВНО 1-2 предложения. НЕ БОЛЬШЕ.
3. Каждое предложение — с фактом, цифрой или интригой.
4. НИКАКОЙ ВОДЫ. Запрещены: «сегодня мы поговорим», «в современном мире», «многие эксперты», «стоит отметить», «это очень важно», «как вы знаете».
5. Если в теме число (Топ-3) — назови РОВНО столько инструментов ПО ИМЕНАМ.
6. Первая сцена — сразу крючок: цифра или вопрос.
7. Последняя сцена — призыв подписаться (1 предложение).

ФОРМАТ (строго):

[SCENE 1]
GROUP: intro
VISUAL: 3-5 english words
TEXT: Одно короткое предложение с цифрой.

[SCENE 2]
GROUP: ChatGPT
VISUAL: person typing laptop
TEXT: Одно предложение. ChatGPT: ...

[SCENE 3]
GROUP: Midjourney
VISUAL: digital art painting
TEXT: Одно предложение. Midjourney: ...

... и так далее, 4-6 сцен.

ВЕРНИ ТОЛЬКО СЦЕНЫ."""

        if feedback:
            prompt += f"\n\nФИДБЕК (исправь):\n{self._truncate(feedback, 400)}"

        return self._ask(role, prompt) or ""

    # ============ КРИТИК ============
    def _critic_shorts(self, script):
        print("   🧐 Критик проверяет...")
        role = "Ты — строгий редактор YouTube Shorts."
        script_short = self._truncate(script, 3000)

        prompt = f"""Оцени сценарий Shorts по критериям (каждый 1-10).

СЦЕНАРИЙ:
{script_short}

КРИТЕРИИ:
1. КОРОТКОСТЬ: каждая сцена 1-2 предложения? (да — 10, 3+ — 1)
2. КОНКРЕТИКА: есть названия, цифры, цены?
3. НЕТ ВОДЫ: нет «сегодня мы поговорим», «в современном мире», «многие эксперты»?
4. СЦЕН: ровно 4-6?
5. КРЮЧОК: первая сцена сразу цепляет?

ФОРМАТ:
ОЦЕНКА: <среднее 1-10>
ВЕРДИКТ: <PASS или FAIL>
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

    # ============ ГЛАВНЫЙ ЦИКЛ SHORTS ============
    def generate_shorts_script(self, topic, niche):
        print(f"\n📝 Генерирую короткий сценарий для: {topic}")
        if not self.client:
            return self._fallback_script(topic, niche)

        research = self._research(topic, niche)
        if research:
            print(f"   ✅ Ресёрч собран ({len(research)} символов)")

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
                print(f"✅ Сценарий принят (оценка {score})")
                break
            print(f"⚠️ Переделка...")

        self.last_score = best_score
        if not best_script:
            return self._fallback_script(topic, niche)

        print(f"✅ Итог: {best_score}/10, {len(best_script)} символов")
        return best_script

    # ============ ИЗВЛЕЧЬ ИНСТРУМЕНТЫ ============
    def extract_tools(self, script):
        tools = set()
        for m in re.finditer(r"GROUP:\s*(.+)", script):
            g = m.group(1).strip()
            if g.lower() not in ("intro", "outro") and len(g) < 30:
                tools.add(g)
        return sorted(tools)

    # ============ SEO ============
    def generate_title_and_description(self, script, niche):
        print("\n🎬 SEO-мастер делает метаданные...")
        if not self.client:
            return {"title": f"{niche}: обзор", "description": script[:200], "tags": [niche]}

        role = "Ты — SEO-специалист YouTube Shorts."
        prompt = f"""Создай метаданные для YouTube Shorts.

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
        return {"title": title or f"{niche}: обзор", "description": description or script[:200], "tags": tags or [niche]}

    def _fallback_script(self, topic, niche):
        return f"""[SCENE 1]
GROUP: intro
VISUAL: person typing laptop
TEXT: 70% людей теряют 3 часа в день на рутину.

[SCENE 2]
GROUP: ChatGPT
VISUAL: person typing laptop chat
TEXT: ChatGPT от OpenAI — бесплатно, плюс 20$ в месяц за Plus.

[SCENE 3]
GROUP: Midjourney
VISUAL: digital art painting
TEXT: Midjourney делает обложку за 5 минут, от 10$ в месяц.

[SCENE 4]
GROUP: outro
VISUAL: subscribe button
TEXT: Подписывайся — дальше больше.
"""
