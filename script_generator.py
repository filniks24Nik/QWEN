import os
import re
from openai import OpenAI

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"

# Лимит бесплатного тарифа Groq — 8000 токенов/мин.
# Безопасный размер промпта — 5000 символов (примерно 4000-5000 токенов).
MAX_PROMPT_CHARS = 5000

MAX_ATTEMPTS = 3
MIN_SCORE = 7


class ScriptGenerator:
    def __init__(self):
        self.client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        if not self.client:
            print("⚠️  GROQ_API_KEY не задан — буду использовать шаблонные тексты.")
        self.last_score = 0

    def _truncate(self, text, max_chars=MAX_PROMPT_CHARS):
        """Обрезает текст до безопасной длины."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n\n[...текст обрезан...]"

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
            print(f"⚠️ Groq ({role[:25]}...): {str(e)[:150]}")
            return None

    # ============ АВТОВЫБОР ТЕМЫ ============
    def pick_best_topic(self, niche, recent_topics=None, recent_tools=None, best_topics=None):
        print(f"\n🧠 Агент выбирает тему для ниши: {niche}")

        recent_topics = recent_topics or []
        recent_tools = recent_tools or []
        best_topics = best_topics or []

        role = "Ты — стратег YouTube-канала. Выбираешь темы, которые зайдут зрителям."
        prompt = f"""Выбери ЛУЧШУЮ тему для YouTube-видео.

НИША: {niche}

УЖЕ ДЕЛАЛИ (не повторяйся):
{chr(10).join(f"- {t}" for t in recent_topics[-10:]) if recent_topics else "ничего ещё"}

ТЕМЫ С ВЫСОКОЙ ОЦЕНКОЙ:
{chr(10).join(f"- {t}" for t in best_topics[-5:]) if best_topics else "нет данных"}

ЗАДАЧА:
1. Придумай 5 РАЗНЫХ тем для видео.
2. Каждая тема — с ЧИСЛОМ (Топ-3, 5 способов).
3. Выбери 1 лучшую.

ФОРМАТ:
ТЕМЫ:
1. <тема>
2. <тема>
3. <тема>
4. <тема>
5. <тема>

ЛУЧШАЯ: <номер>
ПОЧЕМУ: <1 предложение>"""

        result = self._ask(role, prompt, temperature=0.8)
        if not result:
            return "Топ-3 AI для копирайтеров"

        topics = re.findall(r"^\d+\.\s*(.+)$", result, re.MULTILINE)
        best_match = re.search(r"ЛУЧШАЯ:\s*(\d+)", result)
        best_num = int(best_match.group(1)) if best_match else 1

        if topics and 1 <= best_num <= len(topics):
            chosen = topics[best_num - 1].strip()
        elif topics:
            chosen = topics[0].strip()
        else:
            chosen = "Топ-3 AI для копирайтеров"

        print(f"   ✅ Выбрана тема: {chosen}")
        return chosen

    # ============ РОЛЬ 1: РЕСЁРЧЕР ============
    def _research(self, topic, niche):
        print("   🔍 Ресёрчер ищет факты...")
        role = "Ты — исследователь. Собираешь конкретные факты по теме."
        prompt = f"""Собери факты по теме для YouTube-видео.

НИША: {niche}
ТЕМА: {topic}

Верни:
1. 5-7 инструментов с названиями
2. Для каждого: цена (если есть)
3. 2-3 цифры
4. 1-2 минуса

Только факты. Без воды. Максимум 4000 символов."""
        return self._ask(role, prompt, temperature=0.4) or ""

    # ============ РОЛЬ 2: СЦЕНАРИСТ ============
    def _write(self, topic, niche, research, feedback=""):
        print("   ✍️ Сценарист пишет...")
        role = "Ты — опытный сценарист YouTube. Пишешь конкретно, без воды."
        # Обрезаем ресёрч, чтобы не превысить лимит Groq
        research_short = self._truncate(research, 1500)

        prompt = f"""Создай сценарий YouTube-видео на основе исследований.

НИША: {niche}
ТЕМА: {topic}

ИССЛЕДОВАНИЕ:
{research_short}

КРИТИЧЕСКИ ВАЖНО:
1. Если в теме число (Топ-3) — назови РОВНО столько инструментов ПО ИМЕНАМ.
2. Каждый инструмент — ОТДЕЛЬНЫЙ GROUP с его ИМЕНЕМ.
3. Схема: ЧТО → ФУНКЦИИ → ЦЕНА → ПРИМЕР → МИНУС.
4. Каждая сцена — 6-8 предложений.
5. Запрещены: «сегодня мы поговорим», «в современном мире», «многие эксперты».

ФОРМАТ:

[SCENE 1]
GROUP: intro
VISUAL: 3-5 english words
TEXT: 6-8 предложений.

[SCENE 2]
GROUP: ChatGPT
VISUAL: person typing laptop
TEXT: Первое место — ChatGPT. Это...

... и так далее, 12-18 сцен."""

        if feedback:
            prompt += f"\n\nФИДБЕК (исправь):\n{self._truncate(feedback, 500)}"

        return self._ask(role, prompt) or ""

    # ============ РОЛЬ 3: КРИТИК ============
    def _critic(self, script):
        print("   🧐 Критик оценивает...")
        role = "Ты — строгий редактор YouTube."
        # Критик получает только первые 4000 символов сценария
        script_short = self._truncate(script, 4000)

        prompt = f"""Оцени сценарий по 5 критериям (каждый 1-10).

СЦЕНАРИЙ:
{script_short}

КРИТЕРИИ:
1. НАЗВАНИЯ: инструменты названы по именам?
2. ЦИФРЫ: есть цены, статистика?
3. ПРИМЕРЫ: есть кейсы с именами?
4. МИНУСЫ: у каждого инструмента есть минус?
5. ЧИСТОТА: нет фраз «в современном мире», «сегодня мы поговорим»?

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
    def generate_script(self, topic, niche, duration_minutes=10):
        print(f"\n📝 Генерирую сценарий для: {topic}")
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
            script = self._write(topic, niche, research, feedback)
            if not script:
                continue
            score, verdict, feedback = self._critic(script)
            print(f"   Оценка: {score}/10 ({verdict})")
            if score > best_score:
                best_score = score
                best_script = script
            if score >= MIN_SCORE:
                print(f"✅ Сценарий принят (оценка {score})")
                break
            print(f"⚠️ Переделка с фидбеком...")

        self.last_score = best_score

        if not best_script:
            return self._fallback_script(topic, niche)

        print(f"✅ Итог: {best_score}/10, {len(best_script)} символов")
        return best_script

    # ============ ОТБОР СЦЕН ДЛЯ SHORTS ============
    def select_best_scenes(self, script, count=4):
        print(f"\n🎯 Groq выбирает {count} лучших сцен для Shorts...")
        if not self.client:
            return []

        role = "Ты — эксперт по вирусному контенту YouTube Shorts."
        script_short = self._truncate(script, 4000)

        prompt = f"""Выбери {count} САМЫХ ЦЕПЛЯЮЩИХ сцен.

СЦЕНАРИЙ:
{script_short}

КРИТЕРИИ:
1. Есть цифра или интрига.
2. Понятна БЕЗ контекста.

ВЕРНИ ТОЛЬКО НОМЕРА через запятую. Пример: 3, 7, 12, 18"""

        result = self._ask(role, prompt, temperature=0.3)
        if not result:
            return []
        nums = [int(n) for n in re.findall(r"\d+", result)]
        nums = [n for n in nums if 1 <= n <= 100][:count]
        print(f"   ✅ Выбраны сцены: {nums}")
        return nums

    # ============ ИЗВЛЕЧЬ ИНСТРУМЕНТЫ ============
    def extract_tools(self, script):
        tools = set()
        for m in re.finditer(r"GROUP:\s*(.+)", script):
            g = m.group(1).strip()
            if g.lower() not in ("intro", "outro") and len(g) < 30:
                tools.add(g)
        return sorted(tools)

    # ============ SEO-МАСТЕР ============
    def generate_title_and_description(self, script, niche):
        print("\n🎬 SEO-мастер делает метаданные...")
        if not self.client:
            return {"title": f"{niche}: обзор", "description": script[:200], "tags": [niche]}

        role = "Ты — SEO-специалист YouTube."
        script_short = self._truncate(script, 3000)

        prompt = f"""Создай метаданные YouTube.

НИША: {niche}
СЦЕНАРИЙ: {script_short}

ФОРМАТ:
НАЗВАНИЕ: до 60 символов
ОПИСАНИЕ: 100-150 слов
ТЕГИ: тег1, тег2, ... (10 штук)"""

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
TEXT: Привет! Разберём {topic}.

[SCENE 2]
GROUP: ChatGPT
VISUAL: person typing laptop chat
TEXT: Первое место — ChatGPT от OpenAI. Чат-бот на GPT-4. Бесплатно с лимитами, Plus за 20$ в месяц.

[SCENE 3]
GROUP: outro
VISUAL: subscribe youtube button
TEXT: Подписывайся, дальше будет больше.
"""
