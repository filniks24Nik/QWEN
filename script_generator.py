from google import genai
from config import GEMINI_API_KEY

# pro — глубже, flash — быстрее. Начни с pro.
MODEL_NAME = "gemini-3.6-pro"


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
Ты — опытный сценарист YouTube-канала с миллионом подписчиков.
Твоя задача — создать ГЛУБОКИЙ, ИНТЕРЕСНЫЙ сценарий на любую тему.
Не поверхностный обзор, а разбор, после которого зритель чувствует:
«Я узнал что-то новое и могу это применить».

НИША: {niche}
ТЕМА: {topic}
ДЛИТЕЛЬНОСТЬ: примерно {duration_minutes} минут

ЖЕЛЕЗНЫЕ ПРАВИЛА (обязательно):

1. КОНКРЕТИКА ВМЕСТО ОБЩИХ СЛОВ
   - Плохо: «это очень полезно»
   - Хорошо: «экономит 3 часа в неделю, стоит 20$ в месяц»
   - Плохо: «многие эксперты считают»
   - Хорошо: «по данным McKinsey 2024 года, 67% компаний...»
   - Плохо: «в современном мире важно...»
   - Хорошо: сразу к сути

2. КАЖДЫЙ ПУНКТ РАСКРЫВАЕТСЯ ПО СХЕМЕ:
   - ЧТО это (одно предложение)
   - ПОЧЕМУ это важно (проблема, которую решает)
   - КАК это работает или как использовать (пошагово)
   - ПРИМЕР из реальной жизни (с именем, цифрой, результатом)
   - ВЫВОД или предостережение

3. КАЖДАЯ СЦЕНА — 8-10 ПРЕДЛОЖЕНИЙ
   Мало воды, много смысла. Если нечего сказать — объедини сцены.

4. ОБЯЗАТЕЛЬНЫЕ МИНУСЫ
   Для каждого пункта — 1-2 минуса или ограничения.
   Это не реклама, это честный обзор.

5. СТРУКТУРА ВИДЕО:
   - Сцена 1-2: КРЮЧОК. Удивительный факт, вопрос, цифра.
   - Сцена 3-4: ПРОБЛЕМА. Почему тема важна, что теряет зритель без неё.
   - Основная часть: 3-5 крупных блоков, каждый раскрыт в 2-4 сценах.
   - Практика: что делать прямо сегодня, пошагово.
   - Финал: призыв подписаться, тизер следующего видео.

6. ЗАПРЕЩЁННЫЕ ФРАЗЫ (не использовать ни разу):
   - «сегодня мы поговорим о...»
   - «это очень важно»
   - «в современном мире»
   - «многие эксперты считают»
   - «не секрет, что»
   - «стоит отметить»
   - «в заключение хочется сказать»

7. НИКАКОГО MARKDOWN
   Только чистый текст. Без **, ##, ---, ```.

ФОРМАТ ОТВЕТА (строго):

[SCENE 1]
GROUP: intro
VISUAL: 3-5 english words describing a concrete visual subject
TEXT: Текст сцены, 8-10 предложений.

[SCENE 2]
GROUP: intro
VISUAL: ...
TEXT: ...

[SCENE 3]
GROUP: <название подтемы или инструмента>
VISUAL: ...
TEXT: ...

... и так далее, 15-22 сцены.

ПРАВИЛА GROUP:
1. GROUP — это короткое имя подтемы, инструмента, идеи, явления.
   Примеры: ChatGPT, утренние привычки, Древний Рим, инвестиции в акции.
2. Сцены про ОДНУ подтему идут ПОДРЯД и имеют ОДИН GROUP.
3. Для интро GROUP: intro. Для финала: outro.

ПРАВИЛА VISUAL:
1. На английском, 3-5 слов.
2. КОНКРЕТНЫЙ визуальный объект из TEXT этой сцены.
3. Внутри одной группы VISUAL меняется, но остаётся в теме группы.
4. НЕ используй абстракции: technology, business, future, concept.
5. НЕ используй бренды (ChatGPT, Apple) в VISUAL — только общий образ.

ВАЖНО: если тема узкая (например, «как бросить курить»),
используй GROUP по подтемам: «первые 3 дня», «физическая зависимость»,
«психологические триггеры». Это универсальная схема для любой темы.

ВЕРНИ ТОЛЬКО СЦЕНЫ. 15-22 штук. Без пояснений, без вступлений.
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
TEXT: Привет! Сегодня разберём {topic}. Ты узнаешь конкретные вещи с цифрами, примерами и минусами.

[SCENE 2]
GROUP: intro
VISUAL: data charts screen
TEXT: Эта тема касается каждого в нише {niche}. Разберём по шагам.

[SCENE 3]
GROUP: главное
VISUAL: person thinking window
TEXT: Первый аспект темы. Что это, почему важно, как использовать, пример.

[SCENE 4]
GROUP: главное
VISUAL: success achievement
TEXT: Реальный пример с цифрой. Минус и ограничение.

[SCENE 5]
GROUP: outro
VISUAL: subscribe youtube button
TEXT: Подписывайся — в следующих видео разберём ещё больше.
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
