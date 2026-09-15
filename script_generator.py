from google import genai
from config import GEMINI_API_KEY

# gemini-2.5-flash — умнее, чем lite, при этом бесплатная.
MODEL_NAME = "gemini-2.5-flash"


class ScriptGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
        if not self.client:
            print("⚠️  GEMINI_API_KEY не задан — буду использовать шаблонные тексты.")

    def generate_script(self, topic, niche, duration_minutes=10):
        print(f"\n📝 Генерирую сценарий для: {topic}")

        if not self.client:
            return self._fallback_script(topic, niche)

        prompt = f"""
Ты — опытный сценарист YouTube-канала. Создай ГЛУБОКИЙ, СОДЕРЖАТЕЛЬНЫЙ сценарий
на {duration_minutes} минут. Зритель должен узнать КОНКРЕТНЫЕ вещи, а не общие слова.

НИША: {niche}
ТЕМА: {topic}

СТРУКТУРА (обязательно):
1. Сцена 1: Крючок — удивительный факт, цифра или вопрос, который цепляет.
2. Сцены 2-3: Проблема — почему эта тема важна, что теряет человек без неё.
3. Сцены 4-12: Основная часть — 5-7 КОНКРЕТНЫХ пунктов. Каждый пункт:
   - название,
   - что это,
   - как использовать,
   - пример из реальной жизни,
   - результат (цифра/выгода, если возможно).
4. Сцены 13-14: Практика — что делать прямо сегодня, пошагово.
5. Последняя сцена: Призыв подписаться.

ФОРМАТ ОТВЕТА (строго):

[SCENE 1]
VISUAL: 3-5 english words describing the visual subject of THIS scene
TEXT: Текст сцены, 5-7 предложений, с конкретикой.

[SCENE 2]
VISUAL: ...
TEXT: ...

... и так далее, 12-16 сцен.

ПРАВИЛА ДЛЯ ТЕКСТА (очень важно):
1. КОНКРЕТИКА. Вместо «это очень полезно» → «это экономит 3 часа в неделю».
2. ЦИФРЫ И ФАКТЫ. Используй статистику, примеры, названия инструментов.
3. НИКАКОЙ ВОДЫ. Не пиши «сегодня мы поговорим о том, как важно...».
   Сразу переходи к сути.
4. РАЗГОВОРНЫЙ СТИЛЬ, как будто объясняешь другу.
5. Каждая сцена — 5-7 предложений, не меньше.
6. НЕ используй маркдаун (**, ##, ---, ```).

ПРАВИЛА ДЛЯ VISUAL:
1. VISUAL — на английском, 3-5 слов.
2. Описывает КОНКРЕТНЫЙ визуальный объект из TEXT этой сцены.
3. Примеры:
   - «ChatGPT пишет текст» → «person typing laptop keyboard»
   - «нейросеть анализирует данные» → «data charts computer screen»
   - «экономия времени» → «clock business office»
4. НЕ используй абстракции: technology, business, future, concept.
5. НЕ используй бренды (ChatGPT, Canva) — только общий образ.

ВЕРНИ ТОЛЬКО СЦЕНЫ В УКАЗАННОМ ФОРМАТЕ. Без пояснений, без вступлений.
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
TEXT: Привет! Сегодня разберём тему {topic}. Ты узнаешь конкретные шаги, которые можно применить сразу после просмотра.

[SCENE 2]
VISUAL: business meeting room
TEXT: Эта тема касается каждого, кто работает в нише {niche}. По данным исследований, 70% людей теряют время на рутину, которую можно автоматизировать.

[SCENE 3]
VISUAL: data charts screen
TEXT: Первый инструмент — самый важный. Он решает задачу за минуты, а не часы. Вот как его применять: открываешь, настраиваешь, получаешь результат.

[SCENE 4]
VISUAL: office worker smiling
TEXT: Второй инструмент экономит в среднем 5 часов в неделю. Пример: копирайтер сократил время на статьи в 3 раза.

[SCENE 5]
VISUAL: subscribe youtube button
TEXT: Если было полезно — подписывайся на канал. В следующих видео разберём ещё больше конкретных инструментов.
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

НАЗВАНИЕ: цепляющее название до 60 символов, с цифрой или интригой
ОПИСАНИЕ: описание 100-200 слов с ключевыми словами
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
