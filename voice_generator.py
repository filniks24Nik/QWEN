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
        self.rate = "+25%"  # быстрый темп оставляем
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
        print(f"\n🎤 Генерирую озвучку (Edge TTS, rate {self.rate})...")
        self._disable_proxy()

        clean = self._clean_text(text)
        output_path = self.output_dir / filename
        timings_path = output_path.with_suffix(".json")

        try:
            asyncio.run(self._edge_tts(clean, output_path))
            print(f"✅ Озвучка: {output_path}")

            # Whisper для точных тайм-кодов
            self._generate_timings_with_whisper(output_path, timings_path, clean)
            return str(output_path)
        except Exception as e:
            print(f"⚠️ Ошибка Edge TTS: {e}")
            return None

    async def _edge_tts(self, text, output_path):
        communicate = edge_tts.Communicate(
            text, self.voice, rate=self.rate, pitch=self.pitch,
        )
        await communicate.save(str(output_path))

    def _generate_timings_with_whisper(self, audio_path, timings_path, full_text):
        """Запускает faster-whisper на mp3 и строит точные тайм-коды."""
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            print("   ⚠️ faster-whisper не установлен — fallback")
            self._fallback_timings(audio_path, timings_path, full_text)
            return

        try:
            print("   🎧 Whisper анализирует аудио (10-20 сек)...")
            # Модель tiny — быстрая, точности хватает для тайм-кодов
            model = WhisperModel("tiny", device="cpu", compute_type="int8")
            segments, info = model.transcribe(
                str(audio_path),
                language="ru",
                word_timestamps=True,
                vad_filter=True,
            )

            # Собираем все слова с тайм-кодами
            words = []
            for segment in segments:
                if segment.words:
                    for w in segment.words:
                        words.append({
                            "word": w.word.strip(),
                            "start": round(w.start, 2),
                            "end": round(w.end, 2),
                        })

            if not words:
                print("   ⚠️ Whisper не нашёл слова — fallback")
                self._fallback_timings(audio_path, timings_path, full_text)
                return

            # Группируем слова по предложениям
            sentences = self._group_words_to_sentences(words, full_text)

            with open(timings_path, "w", encoding="utf-8") as f:
                json.dump(sentences, f, ensure_ascii=False, indent=2)

            print(f"   ✅ Whisper: точные тайм-коды ({len(sentences)} предложений)")
        except Exception as e:
            print(f"   ⚠️ Whisper ошибка: {str(e)[:120]} — fallback")
            self._fallback_timings(audio_path, timings_path, full_text)

    def _group_words_to_sentences(self, words, full_text):
        """Группирует слова Whisper в предложения по точкам/!/?."""
        sentences_raw = re.split(r"(?<=[.!?])\s+", full_text.strip())
        sentences_raw = [s.strip() for s in sentences_raw if s.strip()]

        result = []
        sent_idx = 0
        current = []

        for w in words:
            current.append(w)
            if w["word"] and w["word"][-1] in ".!?":
                if current and sent_idx < len(sentences_raw):
                    result.append({
                        "text": sentences_raw[sent_idx],
                        "start": current[0]["start"],
                        "end": current[-1]["end"],
                    })
                    sent_idx += 1
                    current = []

        # Остаток
        if current and sent_idx < len(sentences_raw):
            result.append({
                "text": sentences_raw[sent_idx],
                "start": current[0]["start"],
                "end": current[-1]["end"],
            })

        return result

    def _fallback_timings(self, audio_path, timings_path, full_text):
        """Резерв: пропорциональный расчёт."""
        try:
            from moviepy.editor import AudioFileClip
            audio = AudioFileClip(str(audio_path))
            total = audio.duration
            audio.close()
        except Exception:
            return

        sentences = re.split(r"(?<=[.!?])\s+", full_text.strip())
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return

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

        with open(timings_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    def generate_with_emotion(self, text, emotion="neutral", filename="emotional_output.mp3"):
        emotion_settings = {
            "excited": ("+35%", "+20Hz"),
            "calm":    ("+15%", "-10Hz"),
            "serious": ("+20%", "-5Hz"),
            "neutral": ("+25%", "+0Hz"),
        }
        self.rate, self.pitch = emotion_settings.get(emotion, ("+25%", "+0Hz"))
        return self.generate_voice(text, filename)
