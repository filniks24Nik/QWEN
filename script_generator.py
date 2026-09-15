from google import genai
from config import GEMINI_API_KEY

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
Ты — сценарист YouTube-канала про технологии. Создай КОНКРЕТНЫЙ сценарий,
где каждый инструмент/новость/тема раскрывается в НЕСКОЛЬКИХ сценах подряд.
Зритель должен услышать НАЗВАНИЯ инструментов, цифры, примеры.

НИША: {niche}
ТЕМА: {topic}

ГЛАВНАЯ ИДЕЯ ГРУППИРОВКИ:
Если в теме несколько инструментов (например «Топ-5 AI инструментов») —
каждый инструмент раскрывается в 2-4 сценах ПОДРЯД. Все эти сцены имеют
ОДИН И ТОТ ЖЕ GROUP (имя инструмента). Внутри группы сцены развивают тему:
- Сцена 1 группы: что это за инструмент, кто создал, зачем.
- Сцена 2 группы: как использовать, пример из жизни.
- Сцена 3 группы: цена, плюсы, минусы, кому подходит.

СТРУКТУРА:
1. Сцена 1: крючок — удивительный факт или цифра.
2. Сцена 2: проблема — почему тема важна.
3. Группы по инструментам (2-4 сцены на инструмент).
4. Сцена: практика — что делать прямо сегодня.
5. Сцена: призыв подписаться.

ФОРМАТ ОТВЕТА (строго):

[SCENE 1]
GROUP: intro
VISUAL: 3-5 english words describing the visual subject
TEXT: Текст сцены, 5-7 предложений.

[SCENE 2]
GROUP: intro
VISUAL: ...
TEXT: ...

[SCENE 3]
GROUP: ChatGPT
VISUAL: person typing laptop chat
TEXT: Первый инструмент — ChatGPT от OpenAI. Это чат-бот на базе GPT-4...

[SCENE 4]
GROUP: ChatGPT
VISUAL: chat interface screen text
TEXT: ChatGPT умеет писать тексты, отвечать на вопросы, генерировать код...

[SCENE 5]
GROUP: ChatGPT
VISUAL: writer typing office desk
TEXT: Копирайтер Сергей использует ChatGPT для статей. Время сократилось в 3 раза...

[SCENE 6]
GROUP: Midjourney
VISUAL: digital art painting colorful
TEXT: Второй инструмент — Midjourney. Генерирует изображения по тексту...

... и так далее.

ПРАВИЛА GROUP:
1. GROUP — это ОДНО-ТРИ слова: имя инструмента, или "intro", или "outro".
2. Все сцены про ОДИН инструмент идут подряд и имеют ОДИН GROUP.
3. GROUP пишется как есть, без кавычек: `GROUP: ChatGPT`, `GROUP: Midjourney`.
4. Если инструмент на английском (ChatGPT, Midjourney) — пиши по-английски.
5. Если тема не про инструменты (например «привычки») — GROUP — это название подтемы:
   `GROUP: утренние привычки`, `GROUP: вечерние привычки`.

ПРАВИЛА VISUAL:
1. VISUAL — на английском, 3-5 слов.
2. ВНУТРИ ОДНОЙ ГРУППЫ VISUAL меняется, но остаётся в теме инструмента.
   Для ChatGPT: «person typing laptop», «chat screen text», «writer office desk» —
   все про текст/чат/работу. НЕ перескакивай на «city skyline» или «data charts».
3. Для первого VISUAL группы используй образ, связанный с логотипом/интерфейсом.
4. НЕ используй бренды в VISUAL (ChatGPT → «chat interface», не «ChatGPT logo»).
5. НЕ используй абстракции: technology, business, future, concept.

ПРАВИЛА TEXT:
1. КОНКРЕТИКА: называй инструменты по именам.
2. ЦИФРЫ: цены, экономия, статистика.
3. ПРИМЕРЫ: реальные кейсы («маркетолог Анна…»).
4. ЗАПРЕЩЕНЫ фразы: «сегодня мы поговорим о», «это очень важно»,
   «в современном мире», «многие эксперты считают», «стоит отметить».
5. 5-7 предложений на сцену.
6. НЕ используй маркдаун (**, ##, ---, ```).

ВЕРНИ ТОЛЬКО СЦЕНЫ. 12-18 сцен.
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
GROUP: intro
VISUAL: person typing laptop
TEXT: Привет! Сегодня разберём {topic}. Ты узнаешь конкретные инструменты с ценами и примерами.

[SCENE 2]
GROUP: intro
VISUAL: data charts screen
TEXT: Эта тема касается каждого, кто работает в нише {niche}. 70% людей теряют время на рутину, которую можно автоматизировать.

[SCENE 3]
GROUP: ChatGPT
VISUAL: person typing laptop chat
TEXT: Первый инструмент — ChatGPT от OpenAI. Это чат-бот на базе GPT-4. Бесплатная версия доступна всем, платная от 20$ в месяц.

[SCENE 4]
GROUP: ChatGPT
VISUAL: chat interface text screen
TEXT: ChatGPT умеет писать тексты, отвечать на вопросы, генерировать код. Копирайтер Сергей сократил время на статьи в 3 раза.

[SCENE 5]
GROUP: Midjourney
VISUAL: digital art painting colorful
TEXT: Второй — Midjourney. Генерирует изображения по тексту за 30 секунд. Стоит от 10$ в месяц. Дизайнер Ольга делает обложки за 5 минут.

[SCENE 6]
GROUP: Midjourney
VISUAL: designer creative studio
TEXT: Midjourney используют маркетологи, дизайнеры, блогеры. Основной плюс — скорость. Минус — нужен навык промптов.

[SCENE 7]
GROUP: outro
VISUAL: subscribe youtube button
TEXT: Если было полезно — подписывайся. В следующих видео разберём ещё больше инструментов.
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

НАЗВАНИЕ: цепляющее название до 60 символов, с цифрой
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
