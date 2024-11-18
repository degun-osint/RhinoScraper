from typing import Dict, Any
import whois
import socket
import asyncio
from datetime import datetime
from urllib.parse import urlparse
from .base import BaseExtractor


class DomainExtractor(BaseExtractor):
    async def extract(self) -> Dict[str, Any]:
        try:
            domain = urlparse(self.url).netloc
            whois_info = await self._get_whois_info(domain)
            dns_info = await self._get_dns_info(domain)

            return {
                'domain_info': {
                    'whois': whois_info,
                    'dns': dns_info
                }
            }
        except Exception as e:
            print(f"Domain extraction error: {str(e)}")
            return {'domain_info': {}}

    async def _get_whois_info(self, domain: str) -> Dict[str, Any]:
        try:
            w = whois.whois(domain)
            return {
                'registrar': w.registrar,
                'creation_date': str(w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date),
                'expiration_date': str(
                    w.expiration_date[0] if isinstance(w.expiration_date, list) else w.expiration_date)
            }
        except:
            return {}

    async def _get_dns_info(self, domain: str) -> Dict[str, Any]:
        try:
            info = socket.gethostbyname_ex(domain)
            return {
                'hostname': info[0],
                'aliases': info[1],
                'ip_addresses': info[2]
            }
        except:
            return {}

    async def _get_ip_info(self, domain: str) -> Dict[str, Any]:
        """Récupère les informations sur l'IP du domaine"""
        try:
            ip = await asyncio.to_thread(socket.gethostbyname, domain)

            # Informations sur le socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)

            # Test des ports communs
            common_ports = [80, 443, 21, 22, 25, 53]
            open_ports = []

            for port in common_ports:
                try:
                    result = sock.connect_ex((ip, port))
                    if result == 0:
                        open_ports.append(port)
                except:
                    continue

            sock.close()

            return {
                'ip': ip,
                'open_ports': open_ports,
                'reverse_dns': socket.gethostbyaddr(ip)[0] if socket.gethostbyaddr(ip) else None
            }
        except Exception as e:
            return {'error': f"IP lookup failed: {str(e)}"}