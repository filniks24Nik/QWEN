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
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            s = line.strip()
            if not s:
                continue
            if re.match(r"^\[SCENE\s*\d+\]", s, re.IGNORECASE):
                continue
            upper = s.upper()
            if upper.startswith("VISUAL:") or upper.startswith("GROUP:"):
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
        timings_path = output_path.with_suffix(".json")

        try:
            asyncio.run(self._edge_tts(clean, output_path, timings_path))
            print(f"✅ Озвучка (Edge TTS) сохранена: {output_path}")
            return str(output_path)
        except Exception as e:
            print(f"⚠️ Ошибка Edge TTS: {e}")
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

        # Сначала пробуем сгруппировать по WordBoundary
        sentences = self._group_to_sentences(text, word_boundaries)

        # FALLBACK: если не получилось — считаем сами
        if not sentences:
            print("   ℹ️ WordBoundary не пришли — считаю тайм-коды сам")
            sentences = self._fallback_timings(text, output_path)

        with open(timings_path, "w", encoding="utf-8") as f:
            json.dump(sentences, f, ensure_ascii=False, indent=2)
        print(f"✅ Точные тайм-коды субтитров: {timings_path}")

    def _group_to_sentences(self, full_text, boundaries):
        if not boundaries:
            return []

        sentences_raw = re.split(r"(?<=[.!?])\s+", full_text.strip())
        sentences_raw = [s.strip() for s in sentences_raw if s.strip()]

        result = []
        sent_idx = 0
        current = []

        for b in boundaries:
            current.append(b)
            word_text = b["text"].rstrip()
            if word_text and word_text[-1] in ".!?":
                if current and sent_idx < len(sentences_raw):
                    start = current[0]["offset"]
                    last = current[-1]
                    end = last["offset"] + last["duration"]
                    result.append({
                        "text": sentences_raw[sent_idx],
                        "start": round(start, 2),
                        "end": round(end, 2),
                    })
                    sent_idx += 1
                    current = []

        if current and sent_idx < len(sentences_raw):
            start = current[0]["offset"]
            last = current[-1]
            end = last["offset"] + last["duration"]
            result.append({
                "text": sentences_raw[sent_idx],
                "start": round(start, 2),
                "end": round(end, 2),
            })

        return result

    def _fallback_timings(self, full_text, audio_path):
        """Рассчитывает тайм-коды сам: делит длину аудио по длине предложений."""
        try:
            from moviepy.editor import AudioFileClip
            audio = AudioFileClip(str(audio_path))
            total = audio.duration
            audio.close()
        except Exception as e:
            print(f"   ⚠️ Не читать аудио для fallback: {e}")
            return []

        sentences = re.split(r"(?<=[.!?])\s+", full_text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return []

        # Пропорционально длине предложений
        total_chars = sum(len(s) for s in sentences)
        result = []
        current_time = 0.0
        for s in sentences:
            dur = total * (len(s) / total_chars)
            result.append({
                "text": s,
                "start": round(current_time, 2),
                "end": round(current_time + dur, 2),
            })
            current_time += dur
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
