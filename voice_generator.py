import os
import asyncio
import re
from pathlib import Path
import edge_tts


class VoiceGenerator:
    def __init__(self):
        self.output_dir = Path("audio_output")
        self.output_dir.mkdir(exist_ok=True)

        # ru-RU-DmitryNeural  — мужской, спокойный
        # ru-RU-SvetlanaNeural — женский, дружелюбный
        self.voice = "ru-RU-DmitryNeural"
        self.rate = "+0%"
        self.pitch = "+0Hz"

    def _disable_proxy(self):
        """Edge TTS (Microsoft) не работает через VPN-прокси.
        Сбрасываем переменные окружения, чтобы шёл напрямую."""
        for var in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy"):
            os.environ.pop(var, None)

    def _clean_text(self, text):
        """Вырезает служебные маркеры [SCENE N], VISUAL:..., оставляя только TEXT."""
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            s = line.strip()
            if not s:
                continue
            if re.match(r"^\[SCENE\s*\d+\]", s, re.IGNORECASE):
                continue
            if s.upper().startswith("VISUAL:"):
                continue
            if s.upper().startswith("TEXT:"):
                s = s[5:].strip()
            cleaned.append(s)
        return " ".join(cleaned)

    def generate_voice(self, text, filename="output.mp3", use_online=True):
        print(f"\n🎤 Генерирую озвучку (Edge TTS)...")
        self._disable_proxy()
        clean = self._clean_text(text)
        output_path = self.output_dir / filename

        try:
            asyncio.run(self._edge_tts(clean, output_path))
            print(f"✅ Озвучка сохранена: {output_path}")
            return str(output_path)
        except Exception as e:
            print(f"⚠️ Ошибка Edge TTS: {e}")
            return None

    async def _edge_tts(self, text, output_path):
        communicate = edge_tts.Communicate(
            text, self.voice, rate=self.rate, pitch=self.pitch,
        )
        await communicate.save(str(output_path))

    def generate_with_emotion(self, text, emotion="neutral", filename="emotional_output.mp3"):
        emotion_settings = {
            "excited": ("+10%", "+20Hz"),
            "calm":    ("-10%", "-10Hz"),
            "serious": ("-5%",  "-5Hz"),
            "neutral": ("+0%",  "+0Hz"),
        }
        self.rate, self.pitch = emotion_settings.get(emotion, ("+0%", "+0Hz"))
        return self.generate_voice(text, filename)