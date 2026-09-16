import os
from openai import OpenAI

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL_NAME = "openai/gpt-oss-120b"
JUDGE_MODEL = "openai/gpt-oss-120b"

MAX_ATTEMPTS = 3
MIN_SCORE = 7


class ScriptGenerator:
    def __init__(self):
        self.client = OpenAI(base_url=GROQ_BASE_URL, api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        if not self.client:
            print("⚠️  GROQ_API_KEY не задан — буду использовать шаблонные тексты.")

    def _generate(self, prompt, model=None, temperature=0.7):
        try:
            r = self.client.chat.completions.create(
                model=model or MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=8000,
            )
            return r.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Groq ошибка: {e}")
            return None

    def _judge(self, script):
        """Судья оценивает сценарий по 5 критериям. Возвращает (оценка, фидбек)."""
        prompt = f"""Ты — строгий редактор YouTube-канала. Оцени сценарий по 5 критериям.

СЦЕНАРИЙ:
{script}

КРИТЕРИИ (каждый 1-10):
1. НАЗВАНИЯ: названы ли инструменты ПО ИМЕНАМ (ChatGPT, Claude, Midjourney)?
   Если ни одного имени — 1. Если 3+ имени — 8-10.
2. ЦИФРЫ: есть ли цены, экономия времени, статистика?
3. ПРИМЕРЫ: есть ли кейсы с именами людей?
4. МИНУСЫ: у каждого инструмента есть минус/ограничение?
5. ЧИСТОТА: нет ли фраз «в современном мире», «сегодня мы поговорим», «многие эксперты»?

ФОРМАТ ОТВЕТА (строго):
ОЦЕНКА: <среднее 1-10>
ВЕРДИКТ: <PASS если >= 7, FAIL если < 7>
ФИДБЕК: <что конкретно улучшить, 2-3 предложения>"""

        result = self._generate(prompt, model=JUDGE_MODEL, temperature=0.3)
        if not result:
            return 10, "судья недоступен"

        score = 5
        verdict = "PASS"
        feedback = ""
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

    def generate_script(self, topic, niche, duration_minutes=10):
        print(f"\n📝 Генерирую сценарий для: {topic}")
        if not self.client:
            return self._fallback_script(topic, niche)

        base_prompt = f"""Ты — сценарист YouTube-канала про технологии. Создай КОНКРЕТНЫЙ сценарий.
Общие фразы ЗАПРЕЩЕНЫ. Только факты, названия, цифры, примеры.

НИША: {niche}
ТЕМА: {topic}

КРИТИЧЕСКИ ВАЖНО:
1. Если в теме есть число (Топ-5, Топ-3) — назови РОВНО столько инструментов ПО ИМЕНАМ.
2. Называть бренды (ChatGPT, Claude, Midjourney) РАЗРЕШЕНО И ОБЯЗАТЕЛЬНО.
3. На КАЖДЫЙ инструмент — ОТДЕЛЬНЫЙ GROUP с его ИМЕНЕМ.
4. Каждый инструмент раскрыт по схеме: ЧТО → ФУНКЦИИ → ЦЕНА → ПРИМЕР → МИНУС.
5. Каждая сцена — 8-10 предложений.
6. ЗАПРЕЩЕНЫ ФРАЗЫ: «сегодня мы поговорим», «в современном мире», «многие эксперты считают».

ФОРМАТ (строго):

[SCENE 1]
GROUP: intro
VISUAL: 3-5 english words
TEXT: Текст, 8-10 предложений.

[SCENE 2]
GROUP: ChatGPT
VISUAL: person typing laptop
TEXT: Первое место — ChatGPT. Это...

... и так далее, 15-25 сцен."""

        best_script = None
        best_score = 0
        feedback = ""

        for attempt in range(1, MAX_ATTEMPTS + 1):
            print(f"\n   --- Попытка {attempt}/{MAX_ATTEMPTS} ---")

            prompt = base_prompt
            if feedback:
                prompt += f"\n\nФИДБЕК ОТ РЕДАКТОРА (исправь в новой версии):\n{feedback}"

            script = self._generate(prompt)
            if not script:
                continue

            score, verdict, feedback = self._judge(script)
            print(f"   Оценка судьи: {score}/10 ({verdict})")
            if feedback:
                print(f"   Фидбек: {feedback[:100]}...")

            if score > best_score:
                best_score = score
                best_script = script

            if score >= MIN_SCORE:
                print(f"✅ Сценарий принят (оценка {score})")
                return best_script

            print(f"⚠️ Оценка ниже {MIN_SCORE}, перегенерирую с фидбеком...")

        if best_script:
            print(f"⚠️ Лучший результат: {best_score}/10 (после {MAX_ATTEMPTS} попыток)")
            return best_script

        print("❌ Не удалось сгенерировать сценарий")
        return self._fallback_script(topic, niche)

    def _fallback_script(self, topic, niche):
        return f"""[SCENE 1]
GROUP: intro
VISUAL: person typing laptop
TEXT: Привет! Разберём {topic}.

[SCENE 2]
GROUP: ChatGPT
VISUAL: person typing laptop chat
TEXT: Первое место — ChatGPT от OpenAI. Чат-бот на GPT-4, умеет писать тексты и код. Бесплатно с лимитами, Plus за 20$ в месяц. Кейс: копирайтер Сергей сократил время на статьи в 3 раза.

[SCENE 3]
GROUP: outro
VISUAL: subscribe youtube button
TEXT: Подписывайся, дальше будет больше.
"""

    def generate_title_and_description(self, script, niche):
        print("\n🎬 Генерирую название и описание...")
        if not self.client:
            return {"title": f"{niche}: обзор", "description": script[:200], "tags": [niche]}

        prompt = f"""Создай метаданные для YouTube по сценарию.

НИША: {niche}
СЦЕНАРИЙ: {script[:1500]}

ФОРМАТ:
НАЗВАНИЕ: до 60 символов с цифрой
ОПИСАНИЕ: 100-200 слов
ТЕГИ: тег1, тег2, ... (10 штук)"""

        result = self._generate(prompt)
        if not result:
            return {"title": f"{niche}: обзор", "description": script[:200], "tags": [niche]}

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
