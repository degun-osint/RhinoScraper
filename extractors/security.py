import ssl
import socket
import asyncio
import aiohttp
from typing import Dict, Any
from urllib.parse import urlparse
from .base import BaseExtractor


class SecurityExtractor(BaseExtractor):
    async def extract(self) -> Dict[str, Any]:
        try:
            domain = urlparse(self.url).netloc
            ssl_info = await self._get_ssl_info(domain)
            headers = await self._get_security_headers()

            return {
                'security_info': {
                    'ssl': ssl_info,
                    'headers': headers
                }
            }
        except Exception as e:
            print(f"Security extraction error: {str(e)}")
            return {'security_info': {}}

    async def _get_ssl_info(self, domain: str) -> Dict[str, Any]:
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        'issuer': dict(x[0] for x in cert['issuer']),
                        'expiry': cert['notAfter']
                    }
        except Exception as e:
            return {'error': str(e)}

    async def _get_security_headers(self) -> Dict[str, str]:
        headers = {
            'Strict-Transport-Security': 'Missing',
            'Content-Security-Policy': 'Missing',
            'X-Frame-Options': 'Missing'
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    resp_headers = response.headers
                    for header in headers:
                        if header in resp_headers:
                            headers[header] = resp_headers[header]
            return headers
        except Exception as e:
            return {'error': str(e)}