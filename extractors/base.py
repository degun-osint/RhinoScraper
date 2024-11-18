from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import aiohttp

class BaseExtractor(ABC):
    def __init__(self, soup: BeautifulSoup, url: str):
        self.soup = soup
        self.url = url

    @abstractmethod
    async def extract(self) -> Dict[str, Any]:
        pass