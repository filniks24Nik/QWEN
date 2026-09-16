import os
import re
import time
from openai import OpenAI

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"

MAX_ATTEMPTS = 3
MIN_SCORE = 7
MAX_PROMPT_CHARS = 4000
PAUSE_BETWEEN_ITERATIONS = 20  # сек — чтобы не ловить 429


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

    def _ask(self, role, prompt, temperature=0.7, retries=3):
        """С retry при 429."""
        for attempt in range(retries):
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
                err = str(e)
                if "429" in err or "rate_limit" in err.lower():
                    wait = 15 * (attempt + 1)
                    print(f"   ⏳ Лимит Groq, ждём {wait} сек...")
                    time.sleep(wait)
                    continue
                print(f"⚠️ Groq: {err[:150]}")
                return None
        return None

    # ============ АВТОВЫБОР ТЕМЫ ============
    def pick_best_topic(self, niche, recent_topics=None, best_topics=None):
        print(f"\n🧠 Агент выбирает тему: {niche}")
        recent_topics = recent_topics or []

        role = "Ты — стратег YouTube Shorts."
        prompt = f"""Выбери ЛУЧШУЮ тему для Shorts (60 секунд).

НИША: {niche}
УЖЕ ДЕЛАЛИ: {", ".join(recent_topics[-10:]) if recent_topics else "ничего"}

ВАЖНО: тема должна быть про КОНКРЕТНУЮ задачу, не «AI вообще».

ПРИМЕРЫ ХОРОШИХ ТЕМ:
- Как ChatGPT экономит 3 часа в день
- 3 AI-инструмента для копирайтеров
- Почему Midjourney заменяет дизайнера
- Notion AI vs обычные заметки

ЗАДАЧА: придумай 5 тем, выбери 1 лучшую.

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
            return "Как ChatGPT экономит 3 часа в день"

        topics = re.findall(r"^\d+\.\s*(.+)$", result, re.MULTILINE)
        m = re.search(r"ЛУЧШАЯ:\s*(\d+)", result)
        n = int(m.group(1)) if m else 1
        chosen = topics[n - 1].strip() if topics and 1 <= n <= len(topics) else (topics[0].strip() if topics else "Как ChatGPT экономит 3 часа")
        print(f"   ✅ Тема: {chosen}")
        return chosen

    # ============ РЕСЁРЧЕР ============
    def _research(self, topic, niche):
        print("   🔍 Ресёрчер проверяет факты...")
        role = "Ты — исследователь. Знаешь только РЕАЛЬНЫЕ продукты."
        prompt = f"""Собери факты ТОЛЬКО о реально существующих AI-инструментах.

НИША: {niche}
ТЕМА: {topic}

СПИСОК РАЗРЕШЁННЫХ ИНСТРУМЕНТОВ:
ChatGPT, Claude, Gemini, Midjourney, DALL-E, Perplexity, Runway,
Synthesia, ElevenLabs, Notion AI, Copy.ai, Jasper, Leonardo AI,
Suno, HeyGen, Grammarly, DeepL, Otter.ai, Fireflies.

ЖЁСТКИЕ ПРАВИЛА:
1. Используй ТОЛЬКО инструменты из списка.
2. НЕ ПРИДУМЫВАЙ новые названия!
3. Для 3 инструментов укажи:
   - Название
   - Что делает (1 предложение)
   - Цена (бесплатно / от X$ в месяц)
   - Реальный факт (пользователи, экономия времени)

Максимум 1500 символов. Только факты, без воды."""
        return self._ask(role, prompt, temperature=0.3) or ""

    # ============ СЦЕНАРИСТ — СВЯЗНЫЙ РАССКАЗ ============
    def _write_shorts(self, topic, niche, research, feedback=""):
        print("   ✍️ Сценарист пишет связный рассказ...")
        role = "Ты — сценарист YouTube Shorts. Пишешь СВЯЗНЫЙ РАССКАЗ."
        research_short = self._truncate(research, 1200)

        prompt = f"""Напиши сценарий для YouTube Shorts (60-80 секунд).

НИША: {niche}
ТЕМА: {topic}

ИССЛЕДОВАНИЕ:
{research_short}

ГЛАВНОЕ ПРАВИЛО: пиши СВЯЗНЫЙ РАССКАЗ, как будто рассказываешь другу.
Каждое следующее предложение ВЫТЕКАЕТ из предыдущего.

ПРИМЕР ХОРОШЕГО РАССКАЗА (вот так надо):
«Знаете, что копирайтеры тратят 4 часа в день на статьи? Это выматывает.
Но есть решение — ChatGPT. Он пишет черновик за 10 минут, а вы только правите.
Бесплатная версия доступна всем, Plus стоит 20$ в месяц.
Ещё есть Notion AI — он ведёт заметки и планирует день за вас.
Стоит 10$ в месяц, но экономит час ежедневно.
А для обложек есть Midjourney — делает картинку за 5 минут, от 10$ в месяц.
Вот почему 70% фрилансеров уже используют AI.
Попробуйте хотя бы один из них сегодня — и увидите разницу.
Подписывайтесь, дальше разберём ещё больше.»

СТРУКТУРА:
1. Крючок — вопрос или цифра (1 предложение).
2. Проблема — почему это важно (1-2 предложения).
3. Решение через инструмент №1 (2-3 предложения: имя, цена, пример).
4. Решение через инструмент №2 (2-3 предложения).
5. Решение через инструмент №3 (2-3 предложения).
6. Вывод — что делать (1 предложение).
7. Призыв подписаться (1 предложение).

ЗАПРЕЩЕНО:
- Придумывать инструменты (только ChatGPT, Notion AI, Midjourney, Claude, Gemini, Perplexity).
- Водные фразы: «сегодня мы поговорим», «в современном мире», «многие эксперты», «стоит отметить», «важно понимать», «как вы знаете».
- Разрывать рассказ на несвязанные куски.

ФОРМАТ ОТВЕТА (строго):

[SCENE 1]
GROUP: intro
VISUAL: 3-5 english words
TEXT: 1-2 предложения — крючок и проблема.

[SCENE 2]
GROUP: <имя инструмента 1>
VISUAL: 3-5 english words
TEXT: 2-3 предложения про инструмент 1.

[SCENE 3]
GROUP: <имя инструмента 2>
VISUAL: 3-5 english words
TEXT: 2-3 предложения про инструмент 2.

[SCENE 4]
GROUP: <имя инструмента 3>
VISUAL: 3-5 english words
TEXT: 2-3 предложения про инструмент 3 + вывод.

[SCENE 5]
GROUP: outro
VISUAL: subscribe button
TEXT: Призыв подписаться.

ВАЖНО: в каждой сцене — 2-4 предложения. Общий текст — 12-16 предложений.
Верни ТОЛЬКО сцены."""

        if feedback:
            prompt += f"\n\nФИДБЕК ОТ КРИТИКА (исправь обязательно):\n{self._truncate(feedback, 400)}"

        return self._ask(role, prompt) or ""

    # ============ КРИТИК ============
    def _critic_shorts(self, script):
        print("   🧐 Критик проверяет...")
        role = "Ты — строгий редактор YouTube Shorts."
        script_short = self._truncate(script, 3000)

        prompt = f"""Оцени сценарий Shorts (каждый критерий 1-10).

СЦЕНАРИЙ:
{script_short}

КРИТЕРИИ:
1. СВЯЗНОСТЬ (главное!): рассказ идёт по смыслу? Предложения связаны?
   Есть связки «Поэтому», «В итоге», «Ещё есть», «А для...»?
   Если это набор несвязанных фактов — ставь 3 или ниже.
2. РЕАЛЬНОСТЬ ИНСТРУМЕНТОВ: только ChatGPT, Claude, Midjourney, Notion AI,
   Perplexity, Gemini, DALL-E, ElevenLabs? Если есть выдуманные — ставь 1.
3. КОНКРЕТИКА: есть цены, цифры, примеры?
4. НЕТ ВОДЫ: нет «сегодня мы поговорим», «в современном мире»?
5. СТРУКТУРА: есть крючок, проблема, 3 решения, вывод, призыв?

ВАЖНО: текстов 12-16 предложений — это хорошо. Не требуй больше.

ФОРМАТ:
ОЦЕНКА: <среднее 1-10>
ВЕРДИКТ: <PASS если >= 7, FAIL если < 7>
ФИДБЕК: <что конкретно исправить, 2-3 предложения>"""

        result = self._ask(role, prompt, temperature=0.3)
        score, verdict, feedback = 5, "FAIL", ""
        if result:
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

            if attempt > 1:
                print(f"   ⏳ Пауза {PAUSE_BETWEEN_ITERATIONS} сек (лимит Groq)...")
                time.sleep(PAUSE_BETWEEN_ITERATIONS)

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
            print(f"⚠️ Переделка с фидбеком: {feedback[:80]}...")

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
            return {"title": niche, "description": script[:200], "tags": [niche]}

        role = "Ты — SEO-специалист YouTube Shorts."
        prompt = f"""Создай метаданные для Shorts.

НИША: {niche}
СЦЕНАРИЙ: {self._truncate(script, 1500)}

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
        return {"title": title or niche, "description": description or script[:200], "tags": tags or [niche]}

    def _fallback_script(self, topic, niche):
        return f"""[SCENE 1]
GROUP: intro
VISUAL: stressed office worker
TEXT: Знаете, что копирайтеры тратят 4 часа в день на статьи? Это выматывает, и большинство даже не догадываются, что есть решение.

[SCENE 2]
GROUP: ChatGPT
VISUAL: person typing laptop chat
TEXT: Первое — ChatGPT от OpenAI. Он пишет черновик за 10 минут, а вы только правите. Бесплатная версия доступна всем, а Plus стоит 20$ в месяц.

[SCENE 3]
GROUP: Notion AI
VISUAL: notebook organizer screen
TEXT: Второй — Notion AI. Он ведёт заметки и планирует день за вас. Стоит 10$ в месяц, но экономит час ежедневно.

[SCENE 4]
GROUP: Midjourney
VISUAL: digital art painting colorful
TEXT: Третий — Midjourney. Делает обложку за 5 минут, от 10$ в месяц. Вот почему 70% фрилансеров уже используют AI. Попробуйте хотя бы один.

[SCENE 5]
GROUP: outro
VISUAL: subscribe button animation
TEXT: Подписывайтесь — дальше разберём ещё больше AI-лайфхаков.
"""
