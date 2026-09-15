import os
from openai import OpenAI

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL_NAME = "llama-3.3-70b-versatile"


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

НИША: {niche}
ТЕМА: {topic}

КРИТИЧЕСКИ ВАЖНО:
1. Если в теме есть число (Топ-5, Топ-3) — назови РОВНО столько инструментов по именам.
2. Называть бренды (ChatGPT, Claude, Midjourney) РАЗРЕШЕНО И ОБЯЗАТЕЛЬНО.
3. Каждый инструмент раскрыт в 2-3 сценах подряд с одним GROUP.
4. Каждая сцена — 8-10 предложений. Цифры, цены, примеры обязательны.
5. Запрещены фразы: «сегодня мы поговорим», «в современном мире», «многие эксперты».
6. Никакого markdown (без **, ##).

ФОРМАТ (строго):

[SCENE 1]
GROUP: intro
VISUAL: 3-5 english words
TEXT: Текст, 8-10 предложений.

[SCENE 2]
GROUP: ChatGPT
VISUAL: person typing laptop
TEXT: Первое место — ChatGPT. Это...

... и так далее, 15-25 сцен.

ВЕРНИ ТОЛЬКО СЦЕНЫ."""

        script = self._generate(prompt)
        if script:
            print(f"✅ Сценарий сгенерирован ({len(script)} символов)")
            return script
        print("❌ Не удалось, использую fallback")
        return self._fallback_script(topic, niche)

    def _fallback_script(self, topic, niche):
        return f"""[SCENE 1]
GROUP: intro
VISUAL: person typing laptop
TEXT: Привет! Разберём {topic}.

[SCENE 2]
GROUP: ChatGPT
VISUAL: person typing laptop chat
TEXT: Первое место — ChatGPT от OpenAI. Чат-бот на GPT-4, умеет писать тексты и код. Бесплатно с лимитами, Plus за 20$ в месяц.

[SCENE 3]
GROUP: outro
VISUAL: subscribe youtube button
TEXT: Подписывайся, дальше будет больше.
"""

    def generate_title_and_description(self, script, niche):
        print("\n🎬 Генерирую название...")
        if not self.client:
            return {"title": f"{niche}: обзор", "description": script[:200], "tags": [niche]}
        prompt = f"""Создай метаданные для YouTube по сценарию.

НИША: {niche}
СЦЕНАРИЙ: {script[:1000]}

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
