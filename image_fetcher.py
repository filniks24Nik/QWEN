import os
import time
import hashlib
import requests
from pathlib import Path
from urllib.parse import urlparse, urlunparse

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")


class ImageFetcher:
    """
    Ищет картинки:
    1. Если задан group (инструмент) — сначала пробуем найти логотип через Wikipedia
       (хорошо работает для известных брендов: ChatGPT, Claude, Midjourney и т.п.)
    2. Основной источник для VISUAL-сцен — Pexels (настоящий стоковый фотобанк,
       в отличие от Wikimedia Commons понимает обычные бытовые запросы вроде
       "человек печатает на ноутбуке" и на русском, и на английском).
    3. Если Pexels недоступен (нет ключа/лимит) — резервный fallback на
       Wikimedia Commons, чтобы видео всё равно собралось.
    """

    def __init__(self):
        self.cache_dir = Path("image_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "YouTubeFactory/1.0 (contact@example.org) requests/2.34",
        })
        self._last_request_time = 0.0

        if not PEXELS_API_KEY:
            print("⚠️  PEXELS_API_KEY не задан — буду сразу использовать резервный Wikimedia (хуже качество картинок)")

    def _wait(self, seconds=0.5):
        elapsed = time.time() - self._last_request_time
        if elapsed < seconds:
            time.sleep(seconds - elapsed)
        self._last_request_time = time.time()

    def _cache_path(self, key_str, index):
        key = hashlib.md5(f"{key_str}_{index}".lower().encode()).hexdigest()
        return self.cache_dir / f"{key}.jpg"

    def _clean_url(self, url):
        if not url:
            return url
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

    def fetch(self, group, visual, index=0):
        """group — имя инструмента (ChatGPT) или тема (intro).
        visual — конкретный образ сцены."""
        cache_key = f"{group}__{visual}"
        cached = self._cache_path(cache_key, index)
        if cached.exists() and cached.stat().st_size > 1000:
            print(f"📦 Из кэша: {group} / {visual}")
            return str(cached)

        # 1. Логотип инструмента через Wikipedia (для известных брендов)
        if group and group.lower() not in ("intro", "outro"):
            url = self._wikipedia_logo(group)
            if url and self._download(url, cached):
                print(f"✅ Wikipedia logo: {group}")
                return str(cached)

        # 2. Основной источник — Pexels
        if PEXELS_API_KEY:
            url = self._pexels(visual, index)
            if url and self._download(url, cached):
                print(f"✅ Pexels: {visual}")
                return str(cached)

        # 3. Резервный вариант — Wikimedia Commons (fallback 5→1 слово)
        words = visual.split()
        for n in range(min(5, len(words)), 0, -1):
            short_query = " ".join(words[:n])
            url = self._wikimedia_with_retry(short_query, index)
            if url and self._download(url, cached):
                print(f"✅ Wikimedia ({n} сл., резерв): {short_query}")
                return str(cached)

        print(f"❌ Ничего не найдено: {group} / {visual}")
        return None

    def _pexels(self, query, index=0):
        """Ищет фото на Pexels по запросу (понимает и русский, и английский)."""
        try:
            self._wait(0.4)
            r = self.session.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": PEXELS_API_KEY},
                params={"query": query, "per_page": 10, "orientation": "landscape"},
                timeout=30,
            )
            if r.status_code == 429:
                print("⚠️ Pexels: превышен лимит запросов")
                return None
            r.raise_for_status()
            photos = r.json().get("photos", [])
            if not photos:
                return None
            photo = photos[index % len(photos)]
            src = photo.get("src", {})
            return src.get("large2x") or src.get("large") or src.get("original")
        except Exception as e:
            print(f"⚠️ Pexels: {e}")
            return None

    def _wikipedia_logo(self, tool_name):
        for lang in ("en", "ru"):
            try:
                self._wait(0.5)
                r = self.session.get(
                    f"https://{lang}.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "format": "json",
                        "titles": tool_name,
                        "prop": "pageimages",
                        "piprop": "original|thumbnail",
                        "pithumbsize": 1920,
                    },
                    timeout=30,
                )
                if r.status_code != 200:
                    continue
                pages = r.json().get("query", {}).get("pages", {})
                for page in pages.values():
                    thumb = page.get("thumbnail", {})
                    src = thumb.get("source")
                    if src:
                        return self._clean_url(src)
            except Exception as e:
                print(f"⚠️ Wikipedia {lang}: {e}")
        return None

    def _wikimedia_with_retry(self, query, index=0, attempts=2):
        for attempt in range(attempts):
            self._wait(1.0)
            url = self._wikimedia(query, index)
            if url:
                return url
            time.sleep(1.5 * (attempt + 1))
        return None

    def _wikimedia(self, query, index=0):
        try:
            r = self.session.get(
                "https://commons.wikimedia.org/w/api.php",
                params={
                    "action": "query",
                    "format": "json",
                    "generator": "search",
                    "gsrsearch": f"{query} filetype:bitmap",
                    "gsrnamespace": "6",
                    "gsrlimit": 10,
                    "prop": "imageinfo",
                    "iiprop": "url|size",
                    "iiurlwidth": 1920,
                },
                timeout=30,
            )
            if r.status_code == 429:
                return None
            r.raise_for_status()
            pages = r.json().get("query", {}).get("pages", {})
            items = list(pages.values())
            if not items:
                return None
            item = items[index % len(items)]
            info = item.get("imageinfo", [])
            if info:
                raw = info[0].get("thumburl") or info[0].get("url")
                return self._clean_url(raw)
        except Exception as e:
            print(f"⚠️ Wikimedia: {e}")
        return None

    def _download(self, url, save_path):
        try:
            r = self.session.get(url, timeout=40, stream=True)
            r.raise_for_status()
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            return save_path.stat().st_size > 1000
        except Exception as e:
            print(f"⚠️ Не скачалось: {e}")
            return False
