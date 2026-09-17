import os
import hashlib
from pathlib import Path

from huggingface_hub import InferenceClient


class ImageFetcher:
    """
    Генерирует картинки через Flux.1 schnell (Hugging Face).
    Каждая сцена = уникальная AI-картинка по промпту.
    """

    def __init__(self):
        self.cache_dir = Path("image_cache")
        self.cache_dir.mkdir(exist_ok=True)

        hf_token = os.getenv("HF_TOKEN", "")
        self.client = InferenceClient(api_key=hf_token) if hf_token else None
        if not self.client:
            print("⚠️ HF_TOKEN не задан — картинки не будут генерироваться")

        self.model = "black-forest-labs/FLUX.1-schnell"

    def _cache_path(self, prompt, index):
        key = hashlib.md5(f"{prompt}_{index}".lower().encode()).hexdigest()
        return self.cache_dir / f"{key}.jpg"

    def fetch(self, group, visual, index=0):
        """Генерирует картинку через Flux.1 schnell."""
        if not self.client:
            return None

        # Промпт = visual (Groq уже дал детальное описание) + стиль
        prompt = f"{visual}, photorealistic, cinematic lighting, 8k quality, vertical composition"

        cached = self._cache_path(prompt, index)
        if cached.exists() and cached.stat().st_size > 1000:
            print(f"📦 Из кэша: {visual}")
            return str(cached)

        try:
            print(f"🎨 Flux генерирует: {visual[:60]}...")
            image = self.client.text_to_image(
                prompt,
                model=self.model,
                width=768,
                height=1344,  # вертикальный формат под Shorts
            )
            image.save(cached)
            if cached.stat().st_size > 1000:
                print(f"✅ Flux: {visual[:60]}")
                return str(cached)
        except Exception as e:
            print(f"⚠️ Flux: {str(e)[:120]}")

        return None
