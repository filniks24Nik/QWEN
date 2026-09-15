import requests
import json
from datetime import datetime
import pandas as pd
from config import TOP_NICHES_2026, YOUTUBE_API_KEY

class NicheAnalyzer:
    def __init__(self):
        self.api_key = YOUTUBE_API_KEY
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
    def analyze_niche(self, niche_name):
        """Анализирует нишу: конкуренция, тренды, потенциал"""
        print(f"\n🔍 Анализирую нишу: {niche_name}")
        
        # Поиск видео в нише
        search_url = f"{self.base_url}/search"
        params = {
            "part": "snippet",
            "q": niche_name,
            "type": "video",
            "maxResults": 50,
            "order": "viewCount",
            "key": self.api_key
        }
        
        try:
            response = requests.get(search_url, params=params)
            data = response.json()
            
            if "items" not in data:
                return self._analyze_without_api(niche_name)
            
            videos = data["items"]
            
            # Анализ статистики
            total_views = 0
            channel_count = set()
            
            for video in videos:
                total_views += self._get_video_stats(video["id"]["videoId"])
                channel_count.add(video["snippet"]["channelId"])
            
            avg_views = total_views / len(videos) if videos else 0
            
            analysis = {
                "niche": niche_name,
                "total_videos_analyzed": len(videos),
                "avg_views": avg_views,
                "unique_channels": len(channel_count),
                "competition_score": self._calculate_competition(avg_views, len(channel_count)),
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"✅ Анализ завершен:")
            print(f"   - Средние просмотры: {avg_views:,.0f}")
            print(f"   - Уникальных каналов: {len(channel_count)}")
            print(f"   - Оценка конкуренции: {analysis['competition_score']}/10")
            
            return analysis
            
        except Exception as e:
            print(f"⚠️ Ошибка API: {e}")
            return self._analyze_without_api(niche_name)
    
    def _get_video_stats(self, video_id):
        """Получает статистику видео"""
        stats_url = f"{self.base_url}/videos"
        params = {
            "part": "statistics",
            "id": video_id,
            "key": self.api_key
        }
        
        response = requests.get(stats_url, params=params)
        data = response.json()
        
        if "items" in data and len(data["items"]) > 0:
            return int(data["items"][0]["statistics"].get("viewCount", 0))
        return 0
    
    def _calculate_competition(self, avg_views, channel_count):
        """Рассчитывает оценку конкуренции (1-10)"""
        if channel_count > 100 and avg_views > 100000:
            return 9  # Высокая конкуренция
        elif channel_count > 50 and avg_views > 50000:
            return 7  # Средняя конкуренция
        elif channel_count > 20 and avg_views > 10000:
            return 5  # Умеренная конкуренция
        else:
            return 3  # Низкая конкуренция
    
    def _analyze_without_api(self, niche_name):
        """Анализ без API (использует предзагруженные данные)"""
        for niche in TOP_NICHES_2026:
            if niche["name"].lower() in niche_name.lower():
                return {
                    "niche": niche_name,
                    "cpm": niche["cpm"],
                    "competition": niche["competition"],
                    "description": niche["description"],
                    "recommendation": "high" if niche["cpm"] > 15 else "medium"
                }
        
        return {
            "niche": niche_name,
            "cpm": 10,
            "competition": "unknown",
            "recommendation": "medium"
        }
    
    def recommend_niches(self, top_n=5):
        """Рекомендует лучшие ниши на основе анализа"""
        print("\n" + "="*60)
        print("🎯 ТОП НИШИ ДЛЯ YOUTUBE 2026")
        print("="*60)
        
        analyses = []
        
        for niche in TOP_NICHES_2026:
            analysis = self.analyze_niche(niche["name"])
            analysis["cpm"] = niche["cpm"]
            analysis["description"] = niche["description"]
            analyses.append(analysis)
        
        # Сортировка по потенциалу (CPM * обратная конкуренция)
        for a in analyses:
            competition_multiplier = {
                "низкая": 1.5,
                "средняя": 1.0,
                "высокая": 0.7
            }.get(a.get("competition", "средняя"), 1.0)
            
            a["potential_score"] = a["cpm"] * competition_multiplier
        
        # Сортировка
        analyses.sort(key=lambda x: x["potential_score"], reverse=True)
        
        # Вывод топ ниш
        print("\n🏆 РЕКОМЕНДАЦИИ:")
        for i, niche in enumerate(analyses[:top_n], 1):
            print(f"\n{i}. {niche['niche']}")
            print(f"   💰 CPM: ${niche['cpm']}")
            print(f"   📊 Конкуренция: {niche.get('competition', 'N/A')}")
            print(f"   🎯 Потенциал: {niche['potential_score']:.1f}")
            print(f"   📝 {niche['description']}")
        
        return analyses[:top_n]

if __name__ == "__main__":
    analyzer = NicheAnalyzer()
    recommendations = analyzer.recommend_niches(top_n=5)
