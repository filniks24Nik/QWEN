#!/usr/bin/env python3
"""
YouTube Shorts Factory - только вертикальные Shorts
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
from history_manager import HistoryManager


class YouTubeFactory:
    def __init__(self):
        self.niche_analyzer = NicheAnalyzer()
        self.script_generator = ScriptGenerator()
        self.voice_generator = VoiceGenerator()
        self.video_generator = VideoGenerator()
        self.history = HistoryManager()

        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)

    def run_shorts_pipeline(self, niche=None, topic=None):
        print("\n" + "="*60)
        print("🚀 YOUTUBE SHORTS FACTORY")
        print("="*60)

        if not niche:
            print("\n📊 ШАГ 1: Анализ ниш")
            recs = self.niche_analyzer.recommend_niches(top_n=3)
            if recs:
                niche = recs[0]["niche"]
                print(f"\n✅ Ниша: {niche}")
            else:
                print("❌ Не удалось определить нишу")
                return

        if not topic:
            print(f"\n🧠 ШАГ 2: Автовыбор темы")
            recent = self.history.get_recent_topics(limit=20)
            best = self.history.get_best_topics(min_score=8, limit=10)
            print(f"   📚 История: {len(recent)} тем")
            topic = self.script_generator.pick_best_topic(niche, recent, best)

        print(f"\n📝 ШАГ 3: Генерация сценария")
        print(f"Тема: {topic}")

        script = self.script_generator.generate_shorts_script(topic, niche)
        score = self.script_generator.last_score
        tools = self.script_generator.extract_tools(script)
        print(f"🔧 Инструменты: {', '.join(tools)}")

        metadata = self.script_generator.generate_title_and_description(script, niche)

        print(f"\n🎤 ШАГ 4: Озвучка")
        audio_path = self.voice_generator.generate_voice(
            script,
            filename=f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        )

        print(f"\n📱 ШАГ 5: Сборка Shorts")
        shorts_path = self.video_generator.assemble_shorts(
            script,
            audio_path,
            metadata["title"],
            output_filename=f"shorts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        )

        self.history.add_entry(
            niche=niche,
            topic=topic,
            score=score,
            tools=tools,
            video_path=shorts_path,
        )

        result = {
            "timestamp": datetime.now().isoformat(),
            "niche": niche,
            "topic": topic,
            "score": score,
            "tools": tools,
            "title": metadata["title"],
            "description": metadata["description"],
            "tags": metadata["tags"],
            "script": script,
            "audio_path": audio_path,
            "shorts_path": shorts_path,
        }

        result_file = self.data_dir / f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print("\n" + "="*60)
        print("✅ ГОТОВО!")
        print("="*60)
        print(f"\n📱 Shorts: {shorts_path}")
        print(f"🎵 Аудио: {audio_path}")
        print(f"⭐ Оценка: {score}/10")
        print(f"🔧 Инструменты: {', '.join(tools)}")
        print(f"\n🎯 Название: {metadata['title']}")

        return result

    def analyze_and_recommend(self):
        print("\n📊 АНАЛИЗ НИШ")
        recs = self.niche_analyzer.recommend_niches(top_n=5)
        if recs:
            print(f"Лучшая ниша: {recs[0]['niche']}")
        return recs


def main():
    factory = YouTubeFactory()

    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "analyze":
            factory.analyze_and_recommend()
        elif command == "create":
            niche = sys.argv[2] if len(sys.argv) > 2 else None
            topic = sys.argv[3] if len(sys.argv) > 3 else None
            factory.run_shorts_pipeline(niche, topic)
        else:
            print("Команды: analyze | create")
    else:
        factory.run_shorts_pipeline()


if __name__ == "__main__":
    main()
