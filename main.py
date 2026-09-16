#!/usr/bin/env python3
"""
YouTube Content Factory - Автоматическая фабрика контента
"""

import sys
import json
from pathlib import Path
from datetime import datetime

from config import TOP_NICHES_2026, GEMINI_API_KEY
from niche_analyzer import NicheAnalyzer
from script_generator import ScriptGenerator
from voice_generator import VoiceGenerator
from video_generator import VideoGenerator


def check_setup():
    pass


class YouTubeFactory:
    def __init__(self):
        self.niche_analyzer = NicheAnalyzer()
        self.script_generator = ScriptGenerator()
        self.voice_generator = VoiceGenerator()
        self.video_generator = VideoGenerator()

        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    def run_full_pipeline(self, niche=None, topic=None):
        print("\n" + "="*60)
        print("🚀 YOUTUBE CONTENT FACTORY")
        print("="*60)

        if not niche:
            print("\n📊 ШАГ 1: Анализ ниш")
            recommendations = self.niche_analyzer.recommend_niches(top_n=3)
            if recommendations:
                niche = recommendations[0]["niche"]
                print(f"\n✅ Выбрана ниша: {niche}")
            else:
                print("❌ Не удалось определить нишу")
                return

        if not topic:
            topic = self._generate_topic(niche)

        print(f"\n📝 ШАГ 2: Генерация сценария")
        print(f"Тема: {topic}")

        script = self.script_generator.generate_script(topic, niche, duration_minutes=10)
        metadata = self.script_generator.generate_title_and_description(script, niche)

        print(f"\n🎤 ШАГ 3: Генерация озвучки")
        audio_path = self.voice_generator.generate_voice(
            script,
            filename=f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        )

        # ШАГ 4: Длинное видео
        print(f"\n🎬 ШАГ 4: Создание длинного видео")
        video_path = self.video_generator.assemble_video(
            script,
            audio_path,
            metadata["title"],
            output_filename=f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        )

        # ШАГ 5: Shorts
        print(f"\n📱 ШАГ 5: Создание Shorts")
        best_scenes = self.script_generator.select_best_scenes(script, count=4)
        shorts_path = None
        if best_scenes:
            shorts_path = self.video_generator.assemble_shorts(
                script,
                best_scenes,
                audio_path,
                metadata["title"],
                output_filename=f"shorts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            )

        result = {
            "timestamp": datetime.now().isoformat(),
            "niche": niche,
            "topic": topic,
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "script": script,
            "audio_path": audio_path,
            "video_path": video_path,
            "shorts_path": shorts_path,
        }

        result_file = self.data_dir / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print("\n" + "="*60)
        print("✅ ГОТОВО!")
        print("="*60)
        print(f"\n📹 Видео: {video_path}")
        if shorts_path:
            print(f"📱 Shorts: {shorts_path}")
        print(f"🎵 Аудио: {audio_path}")
        print(f"📄 Метаданные: {result_file}")
        print(f"\n🎯 Название: {metadata['title']}")

        return result

    def _generate_topic(self, niche):
        topics_by_niche = {
            "Персональные финансы": [
                "Как накопить первый миллион за год",
                "5 ошибок новичков в инвестициях",
                "Пассивный доход: реальные способы",
            ],
            "AI инструменты и автоматизация": [
                "Топ-3 AI для копирайтеров",
                "Как автоматизировать рутину с помощью AI",
                "AI для контент-мейкеров: полный гайд",
            ],
            "Заработок онлайн": [
                "Фриланс в 2026: с чего начать",
                "Партнерский маркетинг для новичков",
            ],
        }
        import random
        topics = topics_by_niche.get(niche, ["Интересная тема в этой нише"])
        return random.choice(topics)

    def analyze_and_recommend(self):
        print("\n📊 АНАЛИЗ НИШ ДЛЯ YOUTUBE 2026")
        print("="*60)
        recommendations = self.niche_analyzer.recommend_niches(top_n=5)
        print("\n💡 РЕКОМЕНДАЦИЯ:")
        if recommendations:
            best = recommendations[0]
            print(f"Лучшая ниша: {best['niche']}")
        return recommendations


def main():
    check_setup()
    factory = YouTubeFactory()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "analyze":
            factory.analyze_and_recommend()
        elif command == "create":
            niche = sys.argv[2] if len(sys.argv) > 2 else None
            topic = sys.argv[3] if len(sys.argv) > 3 else None
            factory.run_full_pipeline(niche, topic)
        else:
            print("Команды: analyze | create")
    else:
        print("\n🎬 YOUTUBE CONTENT FACTORY")
        print("="*60)
        print("\n1. Анализ ниш")
        print("2. Создать видео")
        print("3. Выход")
        choice = input("\nВаш выбор (1-3): ").strip()
        if choice == "1":
            factory.analyze_and_recommend()
        elif choice == "2":
            factory.run_full_pipeline()
        else:
            print("До свидания!")


if __name__ == "__main__":
    main()
