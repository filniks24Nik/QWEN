import os
import asyncio
import json
import re
from pathlib import Path
import edge_tts


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
        """Вырезает [SCENE N], GROUP:, VISUAL:, оставляя только TEXT."""
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            s = line.strip()
            if not s:
                continue
            if re.match(r"^\[SCENE\s*\d+\]", s, re.IGNORECASE):
                continue
            upper = s.upper()
            if upper.startswith("VISUAL:"):
                continue
            if upper.startswith("GROUP:"):
                continue
            if upper.startswith("TEXT:"):
                s = s[5:].strip()
            cleaned.append(s)
        return " ".join(cleaned)

    def generate_voice(self, text, filename="output.mp3", use_online=True):
        print(f"\n🎤 Генерирую озвучку (Edge TTS)...")
        self._disable_proxy()

        clean = self._clean_text(text)
        output_path = self.output_dir / filename
        # JSON с тайм-кодами предложений рядом с mp3
        timings_path = output_path.with_suffix(".json")

        try:
            asyncio.run(self._edge_tts(clean, output_path, timings_path))
            print(f"✅ Озвучка сохранена: {output_path}")
            if timings_path.exists():
                print(f"✅ Тайм-коды субтитров: {timings_path}")
            return str(output_path)
        except Exception as e:
            print(f"⚠️ Ошибка Edge TTS: {e}")
            return None

    async def _edge_tts(self, text, output_path, timings_path):
        communicate = edge_tts.Communicate(
            text, self.voice, rate=self.rate, pitch=self.pitch,
        )

        # Собираем word boundaries из стрима
        word_boundaries = []

        with open(output_path, "wb") as audio_file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    # offset и duration в единицах 100 наносекунд
                    word_boundaries.append({
                        "text": chunk["text"],
                        "offset": chunk["offset"] / 10_000_000,  # в секунды
                        "duration": chunk["duration"] / 10_000_000,
                    })

        # Группируем слова в предложения и сохраняем тайм-коды
        sentences = self._group_to_sentences(text, word_boundaries)
        with open(timings_path, "w", encoding="utf-8") as f:
            json.dump(sentences, f, ensure_ascii=False, indent=2)

    def _group_to_sentences(self, full_text, boundaries):
        """Группирует слова в предложения, вычисляет start/end каждого."""
        if not boundaries:
            return []

        # Разбиваем полный текст на предложения
        sentences_raw = re.split(r"(?<=[.!?])\s+", full_text.strip())
        sentences_raw = [s.strip() for s in sentences_raw if s.strip()]

        # Идём по словам из boundaries и набираем предложения
        result = []
        sent_idx = 0
        current_sent_words = []

        for b in boundaries:
            current_sent_words.append(b)
            # Проверяем: закончилось ли предложение?
            word_text = b["text"].rstrip()
            if word_text and word_text[-1] in ".!?":
                if current_sent_words and sent_idx < len(sentences_raw):
                    start = current_sent_words[0]["offset"]
                    last = current_sent_words[-1]
                    end = last["offset"] + last["duration"]
                    result.append({
                        "text": sentences_raw[sent_idx],
                        "start": round(start, 2),
                        "end": round(end, 2),
                    })
                    sent_idx += 1
                    current_sent_words = []

        # Остаток — если предложение не закончилось точкой, добавляем
        if current_sent_words and sent_idx < len(sentences_raw):
            start = current_sent_words[0]["offset"]
            last = current_sent_words[-1]
            end = last["offset"] + last["duration"]
            result.append({
                "text": sentences_raw[sent_idx],
                "start": round(start, 2),
                "end": round(end, 2),
            })

        return result

    def generate_with_emotion(self, text, emotion="neutral", filename="emotional_output.mp3"):
        emotion_settings = {
            "excited": ("+10%", "+20Hz"),
            "calm":    ("-10%", "-10Hz"),
            "serious": ("-5%",  "-5Hz"),
            "neutral": ("+0%",  "+0Hz"),
        }
        self.rate, self.pitch = emotion_settings.get(emotion, ("+0%", "+0Hz"))
        return self.generate_voice(text, filename)
