from PIL import Image, ImageDraw, ImageFont

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import *
import numpy as np
from pathlib import Path
import textwrap
import random
import re

from image_fetcher import ImageFetcher


class VideoGenerator:
    def __init__(self):
        self.output_dir = Path("video_output")
        self.output_dir.mkdir(exist_ok=True)

        self.width = 1920
        self.height = 1080
        self.fps = 30

        self.colors = {
            "background": (15, 15, 35),
            "text": (255, 255, 255),
            "accent": (0, 200, 255),
            "highlight": (255, 200, 0),
        }

        self._font_cache = {}
        self.fetcher = ImageFetcher()

        self.music_path = Path("background_music.mp3")
        self.music_volume = 0.12

    def _load_font(self, size):
        if size in self._font_cache:
            return self._font_cache[size]
        candidates = [
            "arial.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        font = None
        for path in candidates:
            try:
                font = ImageFont.truetype(path, size)
                break
            except Exception:
                continue
        if font is None:
            font = ImageFont.load_default()
        self._font_cache[size] = font
        return font

    def _parse_scenes(self, script):
        """Парсит сценарий в список {visual, text}."""
        scenes = []
        blocks = re.split(r"\[SCENE\s*\d+\]", script, flags=re.IGNORECASE)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            visual = ""
            text_lines = []
            for line in block.split("\n"):
                s = line.strip()
                if not s:
                    continue
                if s.upper().startswith("VISUAL:"):
                    visual = s[7:].strip()
                elif s.upper().startswith("TEXT:"):
                    text_lines.append(s[5:].strip())
                else:
                    text_lines.append(s)
            text = " ".join(text_lines).strip()
            if text or visual:
                scenes.append({"visual": visual or "abstract background", "text": text})
        if not scenes:
            scenes = [{"visual": "abstract background", "text": script[:500]}]
        return scenes

    def _ken_burns(self, image_path, duration, direction="in"):
        """Зум (приближение) без CompositeVideoClip — чтобы не терять RGB-каналы."""
        try:
            img_clip = ImageClip(image_path).set_duration(duration)
        except Exception as e:
            print(f"⚠️ Не открыть {image_path}: {e}")
            return ColorClip(size=(self.width, self.height),
                             color=self.colors["background"], duration=duration)

        # Подгоняем под ширину/высоту кадра
        img_clip = img_clip.resize(height=self.height)
        if img_clip.w < self.width:
            img_clip = img_clip.resize(width=self.width)

        # Плавный зум (приближение или удаление)
        if direction == "in":
            zoomed = img_clip.resize(lambda t: 1 + 0.15 * (t / duration))
        else:
            zoomed = img_clip.resize(lambda t: 1.15 - 0.15 * (t / duration))

        # Обрезаем по центру до ровно 1920x1080
        zoomed = zoomed.crop(
            x_center=zoomed.w / 2,
            y_center=zoomed.h / 2,
            width=self.width,
            height=self.height,
        )
        return zoomed.set_duration(duration)

    def _add_text_overlay(self, clip, text, title=""):
        """Рисует текст прямо на кадре клипа (RGB), без CompositeVideoClip с RGBA."""
        font = self._load_font(40)
        title_font = self._load_font(54)
        wrapped = textwrap.fill(text, width=60)
        W, H = self.width, self.height

        def add_text(get_frame, t):
            frame = get_frame(t).copy()
            # Гарантируем 3 канала (RGB)
            if frame.ndim == 2:
                frame = np.stack([frame] * 3, axis=-1)
            elif frame.shape[-1] == 4:
                frame = frame[..., :3]
            img = Image.fromarray(frame).convert("RGBA")
            draw = ImageDraw.Draw(img)

            overlay = Image.new("RGBA", (W, 320), (0, 0, 0, 170))
            img.paste(overlay, (0, H - 320), overlay)

            draw.multiline_text((60, H - 290), wrapped,
                                fill=(255, 255, 255, 255), font=font, align="left")
            if title:
                draw.text((60, 50), title, fill=(0, 200, 255, 255), font=title_font)

            return np.array(img.convert("RGB"))

        return clip.fl(add_text)

    def create_intro(self, title, duration=3):
        def make_frame(t):
            img = Image.new("RGB", (self.width, self.height), self.colors["background"])
            draw = ImageDraw.Draw(img)
            alpha = min(1.0, t / 2)
            font = self._load_font(80)
            bbox = draw.textbbox((0, 0), title, font=font)
            x = (self.width - (bbox[2] - bbox[0])) // 2
            y = self.height // 2 - 50
            color = tuple(int(c * alpha) for c in self.colors["accent"])
            draw.text((x, y), title, fill=color, font=font)
            return np.array(img)
        return VideoClip(make_frame, duration=duration)

    def create_outro(self, duration=3):
        def make_frame(t):
            img = Image.new("RGB", (self.width, self.height), self.colors["background"])
            draw = ImageDraw.Draw(img)
            font = self._load_font(60)
            text = "Подписывайтесь на канал!"
            bbox = draw.textbbox((0, 0), text, font=font)
            x = (self.width - (bbox[2] - bbox[0])) // 2
            draw.text((x, self.height // 2), text, fill=self.colors["highlight"], font=font)
            return np.array(img)
        return VideoClip(make_frame, duration=duration)

    def assemble_video(self, script, audio_path, title, output_filename="final_video.mp4"):
        print(f"\n🎬 Собираю видео...")

        audio = AudioFileClip(audio_path) if audio_path and Path(audio_path).exists() else None
        total_duration = audio.duration if audio else 30

        scenes = self._parse_scenes(script)
        scene_duration = total_duration / max(len(scenes), 1)

        clips = [self.create_intro(title, duration=3)]

        for i, scene in enumerate(scenes):
            img_path = self.fetcher.fetch(scene["visual"], index=i)
            if img_path:
                direction = random.choice(["in", "out"])
                base = self._ken_burns(img_path, scene_duration, direction)
                clip = self._add_text_overlay(base, scene["text"], title=title if i == 0 else "")
            else:
                clip = ColorClip(size=(self.width, self.height),
                                 color=self.colors["background"],
                                 duration=scene_duration)
            clips.append(clip)

        clips.append(self.create_outro(duration=3))
        final_video = concatenate_videoclips(clips, method="compose")

        if audio:
            if final_video.duration < audio.duration:
                diff = audio.duration - final_video.duration
                clips[-1] = clips[-1].set_duration(clips[-1].duration + diff)
                final_video = concatenate_videoclips(clips, method="compose")
            else:
                final_video = final_video.subclip(0, audio.duration)

            tracks = [audio]
            if self.music_path.exists():
                music = AudioFileClip(str(self.music_path)).volumex(self.music_volume)
                if music.duration < final_video.duration:
                    loops_needed = int(final_video.duration / music.duration) + 1
                    music = concatenate_audioclips([music] * loops_needed)
                music = music.subclip(0, final_video.duration)
                tracks.append(music)
                print(f"🎵 Музыка подмешана ({self.music_volume*100:.0f}%)")
            else:
                print("ℹ️ Фоновая музыка не найдена (background_music.mp3)")

            final_video = final_video.set_audio(CompositeAudioClip(tracks))

        output_path = self.output_dir / output_filename
        final_video.write_videofile(
            str(output_path),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
        )
        print(f"✅ Видео сохранено: {output_path}")
        return str(output_path)