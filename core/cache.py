from typing import Any, Optional
from datetime import datetime, timedelta
from diskcache import Cache
import hashlib

class RhinoCache:
    def __init__(self, cache_dir: str = './rhinocache', expiration_days: int = 7):
        self.cache = Cache(cache_dir)
        self.expiration = timedelta(days=expiration_days)

    def _generate_key(self, url: str) -> str:
        """Génère une clé de cache unique pour l'URL"""
        return hashlib.sha256(url.encode()).hexdigest()

    def get(self, url: str) -> Optional[Any]:
        """Récupère les données en cache pour une URL"""
        try:
            key = self._generate_key(url)
            cached_data = self.cache.get(key)
            if cached_data:
                if datetime.now() - datetime.fromisoformat(cached_data['timestamp']) < self.expiration:
                    return cached_data['data']
        except Exception as e:
            print(f"Cache retrieval error: {str(e)}")
        return None

    def set(self, url: str, data: Any) -> None:
        """Stocke les données en cache avec un timestamp"""
        try:
            key = self._generate_key(url)
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            self.cache.set(key, cache_data, expire=int(self.expiration.total_seconds()))
        except Exception as e:
            print(f"Cache storage error: {str(e)}")

    def clear(self) -> None:
        """Vide le cache"""
        try:
            self.cache.clear()
        except Exception as e:
            print(f"Cache clear error: {str(e)}")