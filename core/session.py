from typing import Optional
import aiohttp
import asyncio
from dataclasses import dataclass
import time
from config.settings import Settings  # Import correct

@dataclass
class RateLimiter:
    calls_per_second: int = 2
    _last_call: float = 0
    _lock: asyncio.Lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.time()
            if now - self._last_call < 1.0 / self.calls_per_second:
                await asyncio.sleep(1.0 / self.calls_per_second - (now - self._last_call))
            self._last_call = time.time()

class SessionManager:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter()
        self.settings = Settings.get_instance()  # Utilisation des settings

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.settings.TIMEOUT)
            connector = aiohttp.TCPConnector(
                limit=self.settings.CONCURRENT_REQUESTS,
                force_close=True
            )
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=self.settings.HEADERS
            )
        return self.session

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None