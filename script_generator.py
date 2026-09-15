from google import genai
from config import GEMINI_API_KEY

MODEL_NAME = "gemini-3.1-flash-lite"


class ScriptGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
        if not self.client:
            print("⚠️  GEMINI_API_KEY не задан в .env — буду использовать резервные (шаблонные) тексты.")

    def generate_script(self, topic, niche, duration_minutes=10):
        """Генерирует сценарий с visual prompts, привязанными к содержанию сцены."""
        print(f"\n📝 Генерирую сценарий для: {topic}")

        if not self.client:
            return self._fallback_script(topic, niche)

        prompt = f"""
Ты — режиссёр YouTube-видео. Создай сценарий на {duration_minutes} минут.

НИША: {niche}
ТЕМА: {topic}

ФОРМАТ ОТВЕТА (строго соблюдай):

[SCENE 1]
VISUAL: 3-5 english words that LITERALLY describe the visual subject of this scene
TEXT: Текст сцены на русском, 2-4 предложения.

[SCENE 2]
VISUAL: ...
TEXT: ...

... и так далее, 12-18 сцен.

ПРАВИЛА ДЛЯ VISUAL (ОЧЕНЬ ВАЖНО):
1. VISUAL — ВСЕГДА на английском, 3-5 слов.
2. VISUAL должен описывать КОНКРЕТНЫЙ ВИЗУАЛЬНЫЙ ОБЪЕКТ или ДЕЙСТВИЕ,
   которое реально упоминается в TEXT этой сцены.
3. Примеры:
   - TEXT говорит "ChatGPT помогает писать текст" → VISUAL: "person typing laptop keyboard"
   - TEXT говорит "нейросеть анализирует данные" → VISUAL: "data charts computer screen"
   - TEXT говорит "автоматизация рутины" → VISUAL: "office worker robot arm"
   - TEXT говорит "видеомонтаж" → VISUAL: "video editing timeline screen"
   - TEXT говорит "клиентский сервис" → VISUAL: "call center headset operator"
4. НЕ используй абстрактные слова: "technology", "business", "future", "concept", "innovation".
5. НЕ используй названия брендов (ChatGPT, Canva, Make.com) — ищи общий визуальный образ.
6. НЕ повторяй одинаковые VISUAL в разных сценах.

ПРАВИЛА ДЛЯ TEXT:
- Разговорный стиль, цепляющее вступление, факты, призыв в конце.
- НЕ используй маркдаун (**, ##, ---, ```).
- Первая сцена — интро, последняя — призыв подписаться.
- Каждая сцена — 2-4 предложения, не больше.

ВЕРНИ ТОЛЬКО СЦЕНЫ В УКАЗАННОМ ФОРМАТЕ, без пояснений.
"""

        try:
            response = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            script = response.text
            print(f"✅ Сценарий сгенерирован ({len(script)} символов)")
            return script
        except Exception as e:
            print(f"❌ Ошибка генерации: {e}")
            return self._fallback_script(topic, niche)

    def _fallback_script(self, topic, niche):
        return f"""[SCENE 1]
VISUAL: person typing laptop
TEXT: Привет! Сегодня мы поговорим о теме {topic} в нише {niche}.

[SCENE 2]
VISUAL: business meeting room
TEXT: Это тема, которая интересует многих. Я поделюсь самыми важными моментами.

[SCENE 3]
VISUAL: data charts screen
TEXT: Пункт 1. Важность темы и почему это актуально именно сейчас.

[SCENE 4]
VISUAL: office worker smiling
TEXT: Пункт 2. Практические советы, которые можно применить сразу.

[SCENE 5]
VISUAL: subscribe youtube button
TEXT: Спасибо за просмотр! Подписывайтесь на канал и ставьте лайк.
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

НАЗВАНИЕ: цепляющее название до 60 символов
ОПИСАНИЕ: описание 100-200 слов
ТЕГИ: тег1, тег2, тег3, ... (10 штук)
"""

        try:
            response = self.client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
            )
            result = response.text
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
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            return {
                "title": f"{niche}: обзор",
                "description": script[:200],
                "tags": [niche, "youtube", "автоматизация"],
            }