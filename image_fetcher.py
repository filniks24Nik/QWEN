import time
import hashlib
import requests
from pathlib import Path
from urllib.parse import urlparse, urlunparse


class ImageFetcher:
    """
    Ищет картинки через Wikimedia Commons.
    Fallback: если запрос из 5 слов не найден — пробует 3, потом 2, потом 1.
    """

    def __init__(self):
        self.cache_dir = Path("image_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "YouTubeFactory/1.0 (contact@example.org) requests/2.34",
        })
        self._last_request_time = 0.0

    def _wait(self, seconds=1.0):
        elapsed = time.time() - self._last_request_time
        if elapsed < seconds:
            time.sleep(seconds - elapsed)
        self._last_request_time = time.time()

    def _cache_path(self, query, index):
        key = hashlib.md5(f"{query}_{index}".lower().encode()).hexdigest()
        return self.cache_dir / f"{key}.jpg"

    def _clean_url(self, url):
        if not url:
            return url
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

    def fetch(self, query, index=0):
        if not query or not query.strip():
            return None

        cached = self._cache_path(query, index)
        if cached.exists() and cached.stat().st_size > 1000:
            print(f"📦 Из кэша: {query}")
            return str(cached)

        words = query.split()
        for n in range(min(5, len(words)), 0, -1):
            short_query = " ".join(words[:n])
            url = self._wikimedia_with_retry(short_query, index)
            if url and self._download(url, cached):
                print(f"✅ Wikimedia ({n} сл.): {short_query}")
                return str(cached)
            if n > 1:
                print(f"⚠️ Не найдено «{short_query}», пробую короче...")

        print(f"❌ Ничего не найдено: {query}")
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