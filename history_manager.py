import json
from pathlib import Path
from datetime import datetime


class HistoryManager:
    """Память агента: какие темы делал, какие инструменты упоминал."""

    def __init__(self, path="history.json"):
        self.path = Path(path)
        if not self.path.exists():
            self._save({"topics": [], "tools": []})

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"topics": [], "tools": []}

    def _save(self, data):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_recent_topics(self, limit=20):
        data = self._load()
        return [t["topic"] for t in data.get("topics", [])][-limit:]

    def get_recent_tools(self, limit=30):
        data = self._load()
        return data.get("tools", [])[-limit:]

    def get_best_topics(self, min_score=8, limit=10):
        data = self._load()
        good = [t for t in data.get("topics", []) if t.get("score", 0) >= min_score]
        return [t["topic"] for t in good][-limit:]

    def add_entry(self, niche, topic, score, tools, video_path=None):
        data = self._load()
        data.setdefault("topics", []).append({
            "date": datetime.now().isoformat(),
            "niche": niche,
            "topic": topic,
            "score": score,
            "tools": tools,
            "video_path": video_path,
        })
        existing = set(data.get("tools", []))
        existing.update(tools)
        data["tools"] = sorted(existing)
        self._save(data)
        print(f"💾 История обновлена ({len(data['topics'])} записей)")
