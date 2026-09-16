import os
from openai import OpenAI

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"

MAX_ATTEMPTS = 3
MIN_SCORE = 7


class ScriptGenerator:
    def __init__(self):
        self.client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        if not self.client:
            print("⚠️  GROQ_API_KEY не задан — буду использовать шаблонные тексты.")

    def _ask(self, role, prompt, temperature=0.7):
        """Один вызов LLM с указанием роли."""
        try:
            r = self.client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": role},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=8000,
            )
            return r.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Groq ({role[:20]}...): {e}")
            return None

    # ============ РОЛЬ 1: РЕСЁРЧЕР ============
    def _research(self, topic, niche):
        print("   🔍 Ресёрчер ищет факты...")
        role = "Ты — исследователь. Твоя задача — собрать конкретные факты по теме."
        prompt = f"""Собери факты по теме для YouTube-видео.

НИША: {niche}
ТЕМА: {topic}

Верни:
1. 5-7 конкретных инструментов/сервисов с их названиями и функциями
2. Для каждого: примерная цена (если есть)
3. 2-3 реальные цифры или статистики
4. 1-2 типичных ошибки/минуса

Только факты. Без воды."""
        return self._ask(role, prompt, temperature=0.4) or ""

    # ============ РОЛЬ 2: СЦЕНАРИСТ ============
    def _write(self, topic, niche, research, feedback=""):
        print("   ✍️ Сценарист пишет...")
        role = "Ты — опытный сценарист YouTube. Пишешь конкретно, без воды."
        prompt = f"""Создай сценарий для YouTube-видео на основе исследований.

НИША: {niche}
ТЕМА: {topic}

ИССЛЕДОВАНИЕ (используй эти факты):
{research}

КРИТИЧЕСКИ ВАЖНО:
1. Если в теме число (Топ-3, Топ-5) — назови РОВНО столько инструментов ПО ИМЕНАМ.
2. Каждый инструмент — ОТДЕЛЬНЫЙ GROUP с его ИМЕНЕМ.
3. Схема: ЧТО → ФУНКЦИИ → ЦЕНА → ПРИМЕР → МИНУС.
4. Каждая сцена — 8-10 предложений.
5. Запрещены: «сегодня мы поговорим», «в современном мире», «многие эксперты».

ФОРМАТ:

[SCENE 1]
GROUP: intro
VISUAL: 3-5 english words
TEXT: 8-10 предложений.

[SCENE 2]
GROUP: ChatGPT
VISUAL: person typing laptop
TEXT: Первое место — ChatGPT. Это...

... и так далее, 15-25 сцен."""

        if feedback:
            prompt += f"\n\nФИДБЕК ОТ КРИТИКА (исправь):\n{feedback}"

        return self._ask(role, prompt) or ""

    # ============ РОЛЬ 3: КРИТИК ============
    def _critic(self, script):
        print("   🧐 Критик оценивает...")
        role = "Ты — строгий редактор YouTube. Оцениваешь сценарии по критериям."
        prompt = f"""Оцени сценарий по 5 критериям (каждый 1-10).

СЦЕНАРИЙ:
{script}

КРИТЕРИИ:
1. НАЗВАНИЯ: инструменты названы по именам? (ChatGPT, Claude, Midjourney)
2. ЦИФРЫ: есть цены, экономия времени, статистика?
3. ПРИМЕРЫ: есть кейсы с именами людей?
4. МИНУСЫ: у каждого инструмента есть минус?
5. ЧИСТОТА: нет фраз «в современном мире», «сегодня мы поговорим»?

ФОРМАТ:
ОЦЕНКА: <среднее 1-10>
ВЕРДИКТ: <PASS если >= 7, FAIL если < 7>
ФИДБЕК: <2-3 предложения, что улучшить>"""

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

        # 1. Ресёрч
        research = self._research(topic, niche)
        if research:
            print(f"   ✅ Ресёрч собран ({len(research)} символов)")

        # 2-3-4. Сценарист → Критик → (Редактор = сценарист с фидбеком)
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

        if not best_script:
            return self._fallback_script(topic, niche)

        print(f"✅ Итог: {best_score}/10, {len(best_script)} символов")
        return best_script

    def _fallback_script(self, topic, niche):
        return f"""[SCENE 1]
GROUP: intro
VISUAL: person typing laptop
TEXT: Привет! Разберём {topic}.

[SCENE 2]
GROUP: ChatGPT
VISUAL: person typing laptop chat
TEXT: Первое место — ChatGPT от OpenAI. Чат-бот на GPT-4. Бесплатно с лимитами, Plus за 20$ в месяц. Кейс: копирайтер Сергей сократил время в 3 раза.

[SCENE 3]
GROUP: outro
VISUAL: subscribe youtube button
TEXT: Подписывайся, дальше будет больше.
"""

    # ============ РОЛЬ 5: SEO-МАСТЕР ============
    def generate_title_and_description(self, script, niche):
        print("\n🎬 SEO-мастер делает метаданные...")
        if not self.client:
            return {"title": f"{niche}: обзор", "description": script[:200], "tags": [niche]}

        role = "Ты — SEO-специалист YouTube. Оптимизируешь метаданные под поиск."
        prompt = f"""Создай метаданные для YouTube.

НИША: {niche}
СЦЕНАРИЙ: {script[:2000]}

ФОРМАТ:
НАЗВАНИЕ: до 60 символов, с цифрой или интригой
ОПИСАНИЕ: 150-200 слов с ключевыми словами
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
