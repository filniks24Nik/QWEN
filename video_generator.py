from PIL import Image, ImageDraw, ImageFont

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import *
import numpy as np
from pathlib import Path
import textwrap
import random
import re
import json

from image_fetcher import ImageFetcher


class VideoGenerator:
    def __init__(self):
        self.output_dir = Path("video_output")
        self.output_dir.mkdir(exist_ok=True)

        self.width = 1080
        self.height = 1920
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
        self.music_volume = 0.15

    def _load_font(self, size):
        if size in self._font_cache:
            return self._font_cache[size]
        candidates = [
            "arialbd.ttf",
            "C:\\Windows\\Fonts\\arialbd.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
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
        scenes = []
        blocks = re.split(r"\[SCENE\s*\d+\]", script, flags=re.IGNORECASE)
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            group = ""
            visual = ""
            text_lines = []
            for line in block.split("\n"):
                s = line.strip()
                if not s:
                    continue
                upper = s.upper()
                if upper.startswith("GROUP:"):
                    group = s[6:].strip()
                elif upper.startswith("VISUAL:"):
                    visual = s[7:].strip()
                elif upper.startswith("TEXT:"):
                    text_lines.append(s[5:].strip())
                else:
                    text_lines.append(s)
            text = " ".join(text_lines).strip()
            if text or visual:
                scenes.append({
                    "group": group or "intro",
                    "visual": visual or "abstract background",
                    "text": text,
                })
        if not scenes:
            scenes = [{"group": "intro", "visual": "abstract background", "text": script[:500]}]
        return scenes

    def _load_subtitles(self, audio_path):
        if not audio_path:
            return []
        json_path = Path(audio_path).with_suffix(".json")
        if not json_path.exists():
            return []
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _find_current_sentence(self, subtitles, t):
        for s in subtitles:
            if s["start"] <= t <= s["end"]:
                return s["text"]
        return None

    def _ken_burns(self, image_path, duration, direction="in"):
        try:
            img_clip = ImageClip(image_path).set_duration(duration)
        except Exception:
            return ColorClip(size=(self.width, self.height),
                             color=self.colors["background"], duration=duration)
        img_clip = img_clip.resize(height=self.height)
        if img_clip.w < self.width:
            img_clip = img_clip.resize(width=self.width)
        if direction == "in":
            zoomed = img_clip.resize(lambda t: 1 + 0.15 * (t / duration))
        else:
            zoomed = img_clip.resize(lambda t: 1.15 - 0.15 * (t / duration))
        zoomed = zoomed.crop(
            x_center=zoomed.w / 2,
            y_center=zoomed.h / 2,
            width=self.width,
            height=self.height,
        )
        return zoomed.set_duration(duration)

    def _draw_text_with_outline(self, draw, x, y, text, font,
                                 fill=(255, 255, 255, 255),
                                 outline=(0, 0, 0, 255),
                                 outline_width=4):
        for dx in range(-outline_width, outline_width + 1):
            for dy in range(-outline_width, outline_width + 1):
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), text, font=font, fill=outline)
        draw.text((x, y), text, font=font, fill=fill)

    def _add_subtitle(self, clip, subtitles, global_start, scene_text):
        font = self._load_font(58)
        W, H = self.width, self.height

        def add_text(get_frame, t):
            frame = get_frame(t).copy()
            if frame.ndim == 2:
                frame = np.stack([frame] * 3, axis=-1)
            elif frame.shape[-1] == 4:
                frame = frame[..., :3]
            img = Image.fromarray(frame).convert("RGBA")
            draw = ImageDraw.Draw(img)

            text = None
            if subtitles:
                text = self._find_current_sentence(subtitles, global_start + t)
            if not text:
                text = scene_text

            if text:
                wrapped = textwrap.fill(text, width=30)
                lines = wrapped.split("\n")

                line_heights = []
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_heights.append(bbox[3] - bbox[1])
                total_h = sum(line_heights) + (len(lines) - 1) * 10

                y_start = H - 180 - total_h

                for i, line in enumerate(lines):
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_w = bbox[2] - bbox[0]
                    x = (W - line_w) // 2
                    y = y_start + sum(line_heights[:i]) + i * 10
                    self._draw_text_with_outline(
                        draw, x, y, line, font,
                        fill=(255, 255, 255, 255),
                        outline=(0, 0, 0, 255),
                        outline_width=4,
                    )
            return np.array(img.convert("RGB"))

        return clip.fl(add_text)

    def assemble_shorts(self, script, audio_path, title, output_filename="shorts.mp4"):
        print(f"\n📱 Собираю Shorts...")

        audio = AudioFileClip(audio_path) if audio_path and Path(audio_path).exists() else None
        total_duration = audio.duration if audio else 60

        subtitles = self._load_subtitles(audio_path)
        if subtitles:
            print(f"📝 Загружено {len(subtitles)} предложений для субтитров")
        else:
            print("ℹ️ Тайм-коды не найдены — субтитры = текст сцены")

        scenes = self._parse_scenes(script)
        print(f"📊 Сцен: {len(scenes)}")

        scene_duration = total_duration / max(len(scenes), 1)
        print(f"⏱ Каждая сцена: {scene_duration:.1f} сек")

        clips = []
        global_start = 0.0

        for i, scene in enumerate(scenes):
            img_path = self.fetcher.fetch(scene["group"], scene["visual"], index=i)
            if img_path:
                direction = random.choice(["in", "out"])
                base = self._ken_burns(img_path, scene_duration, direction)
            else:
                base = ColorClip(size=(self.width, self.height),
                                 color=self.colors["background"],
                                 duration=scene_duration)
            clip = self._add_subtitle(base, subtitles, global_start, scene["text"])
            clips.append(clip)
            global_start += scene_duration

        final = concatenate_videoclips(clips, method="compose")

        if audio:
            if final.duration < audio.duration:
                final = final.set_duration(audio.duration)
            else:
                final = final.subclip(0, audio.duration)

            tracks = [audio]
            if self.music_path.exists():
                music = AudioFileClip(str(self.music_path)).volumex(self.music_volume)
                if music.duration < final.duration:
                    loops = int(final.duration / music.duration) + 1
                    music = concatenate_audioclips([music] * loops)
                music = music.subclip(0, final.duration)
                tracks.append(music)
                print(f"🎵 Музыка подмешана ({self.music_volume*100:.0f}%)")

            final = final.set_audio(CompositeAudioClip(tracks))

        output_path = self.output_dir / output_filename
        final.write_videofile(
            str(output_path),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-shorts.m4a",
            remove_temp=True,
        )
        print(f"✅ Shorts сохранён: {output_path}")
        return str(output_path)
