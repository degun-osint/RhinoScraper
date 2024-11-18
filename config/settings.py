# config/settings.py
from typing import Dict, Any
from dataclasses import dataclass, field


@dataclass
class Settings:
    MAX_RETRIES: int = 3
    TIMEOUT: int = 20
    MAX_DEPTH: int = 3
    CONCURRENT_REQUESTS: int = 3
    CACHE_DURATION: int = 7
    MAX_LINKS_PER_LEVEL: int = 10

    HEADERS: Dict[str, Any] = field(default_factory=lambda: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })

    @classmethod
    def get_instance(cls) -> 'Settings':
        """Retourne une instance singleton des paramètres"""
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance