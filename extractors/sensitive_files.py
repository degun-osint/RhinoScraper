import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
import async_timeout
from .base import BaseExtractor


class SensitiveFileExtractor(BaseExtractor):
    def __init__(self, soup, url):
        super().__init__(soup, url)
        self.sensitive_paths = [
            'robots.txt', '.git/HEAD', '.env', 'wp-config.php',
            '.htaccess', '.htpasswd', 'config.php', 'sitemap.xml',
            'administrator/', 'admin/', '.DS_Store', 'backup/',
            'phpinfo.php', '.svn/', 'credentials.txt',
            '.bash_history', 'backup.sql', 'debug.log'
        ]

    async def extract(self) -> Dict[str, List[Dict[str, Any]]]:
        """Vérifie la présence de fichiers sensibles"""
        try:
            exposed_files = []
            base_url = self.url.rstrip('/')

            async with aiohttp.ClientSession() as session:
                tasks = []
                for path in self.sensitive_paths:
                    url = f"{base_url}/{path}"
                    tasks.append(self._check_path(session, url, path))

                results = await asyncio.gather(*tasks, return_exceptions=True)
                exposed_files = [r for r in results if r and not isinstance(r, Exception)]

            return {'sensitive_files': exposed_files}

        except Exception as e:
            print(f"Sensitive files extraction error: {str(e)}")
            return {'sensitive_files': []}

    async def _check_path(self, session: aiohttp.ClientSession, url: str, path: str) -> Optional[Dict[str, Any]]:
        try:
            async with session.head(url, allow_redirects=False, ssl=False) as response:
                if response.status in [200, 403]:
                    return {
                        'path': path,
                        'status': response.status,
                        'url': url,
                        'risk_level': 'HIGH' if any(x in path for x in ['.env', 'config', 'credentials'])
                        else 'MEDIUM'
                    }
        except Exception as e:
            print(f"Error checking path {path}: {str(e)}")
            return None