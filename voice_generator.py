import os
import re
import json
import asyncio
from pathlib import Path

import edge_tts
from gtts import gTTS


class VoiceGenerator:
    def __init__(self):
        self.output_dir = Path("audio_output")
        self.output_dir.mkdir(exist_ok=True)
        self.voice = "ru-RU-DmitryNeural"
        self.rate = "+0%"
        self.pitch = "+0Hz"

    def _disable_proxy(self):
        for var in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
            os.environ.pop(var, None)

    def _clean_text(self, text):
        """Вырезает [SCENE N], GROUP:, VISUAL:, оставляя только TEXT.
        Заодно снимает случайный markdown (**...**), который иногда
        добавляет Groq и который не должен попадать в озвучку/субтитры."""
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            s = line.strip()
            if not s:
                continue
            if re.match(r"^\[SCENE\s*\d+\]", s, re.IGNORECASE):
                continue
            # снимаем markdown-звёздочки перед проверкой лейблов
            s_plain = re.sub(r"\*{1,2}|_{1,2}", "", s).strip()
            upper = s_plain.upper()
            if upper.startswith("VISUAL:"):
                continue
            if upper.startswith("GROUP:"):
                continue
            if upper.startswith("TEXT:"):
                s_plain = s_plain[5:].strip()
            cleaned.append(s_plain)
        return " ".join(cleaned)

    def generate_voice(self, text, filename="output.mp3", use_online=True):
        print(f"\n🎤 Генерирую озвучку...")
        self._disable_proxy()

        clean = self._clean_text(text)
        output_path = self.output_dir / filename
        timings_path = output_path.with_suffix(".json")

        # 1. Пробуем Edge TTS (даёт точную посекундную синхронизацию по словам)
        for attempt in range(1, 3):
            try:
                asyncio.run(self._edge_tts(clean, output_path, timings_path))
                if output_path.exists() and output_path.stat().st_size > 1000:
                    print(f"✅ Озвучка (Edge TTS) сохранена: {output_path}")
                    if timings_path.exists():
                        print(f"✅ Точные тайм-коды субтитров: {timings_path}")
                    return str(output_path)
            except Exception as e:
                print(f"⚠️ Edge TTS, попытка {attempt}/2: {e}")

        # 2. Резерв — gTTS (Google Translate TTS). Реже блокируется на
        #    облачных IP (GitHub Actions и т.п.), но не даёт тайм-коды по
        #    словам — оценим тайминг предложений пропорционально их длине.
        print("⚠️ Edge TTS недоступен — переключаюсь на резервный gTTS...")
        try:
            gTTS(text=clean, lang="ru").save(str(output_path))
            if output_path.exists() and output_path.stat().st_size > 1000:
                print(f"✅ Озвучка (gTTS, резерв) сохранена: {output_path}")
                self._write_estimated_timings(clean, output_path, timings_path)
                return str(output_path)
        except Exception as e:
            print(f"❌ Ошибка gTTS: {e}")

        print("❌ Не удалось сгенерировать озвучку ни одним способом")
        return None

    async def _edge_tts(self, text, output_path, timings_path):
        communicate = edge_tts.Communicate(
            text, self.voice, rate=self.rate, pitch=self.pitch,
        )
        word_boundaries = []
        with open(output_path, "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    word_boundaries.append({
                        "text": chunk["text"],
                        "offset": chunk["offset"] / 10_000_000,
                        "duration": chunk["duration"] / 10_000_000,
                    })

        if not output_path.exists() or output_path.stat().st_size < 1000:
            raise RuntimeError("No audio was received. Please verify that your parameters are correct.")

        sentences = self._group_to_sentences(text, word_boundaries)
        with open(timings_path, "w", encoding="utf-8") as f:
            json.dump(sentences, f, ensure_ascii=False, indent=2)

    def _group_to_sentences(self, full_text, boundaries):
        if not boundaries:
            return []
        sentences_raw = re.split(r"(?<=[.!?])\s+", full_text.strip())
        sentences_raw = [s.strip() for s in sentences_raw if s.strip()]

        result = []
        sent_idx = 0
        current_sent_words = []
        for b in boundaries:
            current_sent_words.append(b)
            word_text = b["text"].rstrip()
            if word_text and word_text[-1] in ".!?":
                if current_sent_words and sent_idx < len(sentences_raw):
                    start = current_sent_words[0]["offset"]
                    last = current_sent_words[-1]
                    end = last["offset"] + last["duration"]
                    result.append({"text": sentences_raw[sent_idx], "start": round(start, 2), "end": round(end, 2)})
                    sent_idx += 1
                    current_sent_words = []
        if current_sent_words and sent_idx < len(sentences_raw):
            start = current_sent_words[0]["offset"]
            last = current_sent_words[-1]
            end = last["offset"] + last["duration"]
            result.append({"text": sentences_raw[sent_idx], "start": round(start, 2), "end": round(end, 2)})
        return result

    def _write_estimated_timings(self, full_text, audio_path, timings_path):
        """Резервный расчёт тайм-кодов для gTTS: делим общую длительность
        аудио между предложениями пропорционально их длине в символах."""
        try:
            from moviepy.editor import AudioFileClip
            total_duration = AudioFileClip(str(audio_path)).duration
        except Exception as e:
            print(f"⚠️ Не удалось определить длительность аудио: {e}")
            return

        sentences_raw = re.split(r"(?<=[.!?])\s+", full_text.strip())
        sentences_raw = [s.strip() for s in sentences_raw if s.strip()]
        if not sentences_raw:
            return

        total_chars = sum(len(s) for s in sentences_raw) or 1
        result = []
        t = 0.0
        for s in sentences_raw:
            dur = total_duration * (len(s) / total_chars)
            result.append({"text": s, "start": round(t, 2), "end": round(t + dur, 2)})
            t += dur

        with open(timings_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"✅ Оценочные тайм-коды субтитров (по длине предложений): {timings_path}")

    def generate_with_emotion(self, text, emotion="neutral", filename="emotional_output.mp3"):
        emotion_settings = {
            "excited": ("+10%", "+20Hz"),
            "calm":    ("-10%", "-10Hz"),
            "serious": ("-5%",  "-5Hz"),
            "neutral": ("+0%",  "+0Hz"),
        }
        self.rate, self.pitch = emotion_settings.get(emotion, ("+0%", "+0Hz"))
        return self.generate_voice(text, filename)
