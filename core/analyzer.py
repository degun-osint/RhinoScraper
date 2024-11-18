from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse, urljoin
import asyncio
from bs4 import BeautifulSoup
import aiohttp
from config.settings import Settings

from core.session import SessionManager
from core.cache import RhinoCache
from extractors import (
    ContentExtractor,
    SecurityExtractor,
    SocialExtractor,
    DomainExtractor,
    EmailExtractor,
    PhoneExtractor,
    TechnologyExtractor,
    SensitiveFileExtractor
)


@dataclass
class AnalysisResult:
    """Structure de données pour les résultats d'analyse"""
    url: str
    status_code: int
    analyzed_at: str
    content: Dict[str, Any]
    security: Dict[str, Any]
    social: Dict[str, Any]
    domain: Dict[str, Any]
    emails: List[Dict[str, str]]
    phones: List[str]
    technologies: List[str]
    sensitive_files: List[Dict[str, Any]]
    internal_links: Dict[str, Any]


class SiteAnalyzer:
    def __init__(self, session_manager: SessionManager, cache: RhinoCache):
        self.session_manager = session_manager
        self.cache = cache
        self.settings = Settings.get_instance()
        self.analyzed_urls: Set[str] = set()

    async def analyze(self, url: str, depth: int = 0) -> Optional[AnalysisResult]:
        """Analyse complète d'une URL avec tous les extracteurs"""
        try:
            if url in self.analyzed_urls or depth > self.settings.MAX_DEPTH:
                return None

            if cached_result := self.cache.get(url):
                return cached_result

            print(f"Analyzing URL: {url} at depth {depth}")  # Debug
            self.analyzed_urls.add(url)

            session = await self.session_manager.get_session()
            async with session.get(url, ssl=False) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                # Création des instances d'extracteurs
                extractors = [
                    ContentExtractor(soup, url),
                    SecurityExtractor(soup, url),
                    SocialExtractor(soup, url),
                    DomainExtractor(soup, url),
                    EmailExtractor(soup, url),
                    PhoneExtractor(soup, url),
                    TechnologyExtractor(soup, url),
                    SensitiveFileExtractor(soup, url),  # Suppression du paramètre session
                ]

                # Exécution parallèle des extracteurs
                results = await asyncio.gather(
                    *[extractor.extract() for extractor in extractors],
                    return_exceptions=True
                )

                # Traitement des résultats
                combined_results = {}
                for result in results:
                    if isinstance(result, Exception):
                        print(f"Extractor error: {str(result)}")
                        continue
                    if isinstance(result, dict):
                        combined_results.update(result)

                # Analyse récursive des liens internes si nécessaire
                internal_links = {}
                if depth < self.settings.MAX_DEPTH:
                    found_links = self._get_internal_links(soup, url)
                    print(f"Found {len(found_links)} internal links")
                    if found_links:  # Ne procéder que s'il y a des liens à analyser
                        internal_links = await self._analyze_internal_links(found_links, depth + 1)

                # Construction du résultat final
                analysis_result = AnalysisResult(
                    url=url,
                    status_code=response.status,
                    analyzed_at=datetime.now().isoformat(),
                    content=combined_results.get('content', {}),
                    security=combined_results.get('security_info', {}),
                    social=combined_results.get('social_media', {}),
                    domain=combined_results.get('domain_info', {}),
                    emails=combined_results.get('emails', []),
                    phones=combined_results.get('phones', []),
                    technologies=combined_results.get('technologies', []),
                    sensitive_files=combined_results.get('sensitive_files', []),
                    internal_links=internal_links
                )

                self.cache.set(url, analysis_result)
                return analysis_result

        except aiohttp.ClientError as e:

            print(f"Network error analyzing {url}: {str(e)}")

            return None

        except Exception as e:

            print(f"Error analyzing {url}: {str(e)}")

            return None

    def _get_internal_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """Extrait les liens internes de la page"""
        internal_links = set()
        base_domain = urlparse(base_url).netloc.replace('www.', '')  # Supprime le www pour la comparaison

        print(f"Base domain: {base_domain}")  # Debug

        for a in soup.find_all('a', href=True):
            href = a['href'].strip()

            # Ignorer les liens vides ou spéciaux
            if not href or any(href.startswith(prefix) for prefix in ('mailto:', 'tel:', 'javascript:', '#')):
                continue

            try:
                # Convertir l'URL relative en absolue
                full_url = urljoin(base_url, href)
                parsed_url = urlparse(full_url)

                # Normaliser le domaine pour la comparaison (enlever le www si présent)
                url_domain = parsed_url.netloc.replace('www.', '')

                # Vérifier que c'est un lien HTTP(S) et interne
                if (parsed_url.scheme in ('http', 'https') and
                        url_domain == base_domain and
                        full_url not in internal_links):  # Éviter les doublons
                    print(f"Found internal link: {full_url}")  # Debug
                    internal_links.add(full_url)
            except Exception as e:
                print(f"Error processing URL {href}: {str(e)}")
                continue

        print(f"Total internal links found: {len(internal_links)}")  # Debug
        return internal_links

    async def _analyze_internal_links(self,
                                      links: Set[str],
                                      depth: int) -> Dict[str, Any]:
        """Analyse récursive des liens internes"""
        print(f"Analyzing {len(links)} links at depth {depth}")

        if depth > self.settings.MAX_DEPTH:
            return {}

        # Filtrer les liens déjà analysés
        new_links = [link for link in links if link not in self.analyzed_urls]
        print(f"New links to analyze: {len(new_links)}")  # Debug

        # Trier les liens pour assurer une cohérence dans l'analyse
        links_to_process = sorted(new_links)[:self.settings.MAX_LINKS_PER_LEVEL]
        print(f"Links selected for processing: {len(links_to_process)}")  # Debug

        if not links_to_process:
            return {}

        tasks = []
        for link in links_to_process:
            if link not in self.analyzed_urls:
                tasks.append(self.analyze(link, depth))

        results = []
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Construire le dictionnaire des résultats
        analyzed_links = {}
        for link, result in zip(links_to_process, results):
            if not isinstance(result, Exception) and result is not None:
                analyzed_links[link] = result
                print(f"Successfully analyzed: {link}")  # Debug

        return analyzed_links