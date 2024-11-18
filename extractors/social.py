# extractors/social.py
import re
from typing import Dict, Any, Set
from .base import BaseExtractor

class SocialExtractor(BaseExtractor):
    def __init__(self, soup, url):
        super().__init__(soup, url)
        self.social_patterns = {
            'facebook': [
                r'facebook\.com/[A-Za-z0-9.]+',
                r'fb\.com/[A-Za-z0-9.]+',
                r'facebook\.com/profile\.php\?id=\d+'
            ],
            'twitter': [
                r'twitter\.com/[A-Za-z0-9_]+',
                r'x\.com/[A-Za-z0-9_]+'
            ],
            'linkedin': [
                r'linkedin\.com/company/[A-Za-z0-9_-]+',
                r'linkedin\.com/in/[A-Za-z0-9_-]+'
            ],
            'instagram': [
                r'instagram\.com/[A-Za-z0-9_.]+',
                r'instagr\.am/[A-Za-z0-9_.]+'
            ]
        }

    async def extract(self) -> Dict[str, Dict[str, Any]]:
        """Extrait tous les liens de réseaux sociaux de la page"""
        try:
            social_links = {}
            html_content = str(self.soup)

            for platform, patterns in self.social_patterns.items():
                found_links = set()
                for pattern in patterns:
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    found_links.update(matches)

                if found_links:
                    social_links[platform] = {
                        'links': list(found_links),
                        'count': len(found_links)
                    }

            # Recherche dans les méta-tags spécifiques aux réseaux sociaux
            meta_social = self._extract_meta_social()

            return {
                'social_media': {
                    'links': social_links,
                    'meta': meta_social
                }
            }
        except Exception as e:
            print(f"Social extraction error: {str(e)}")
            return {'social_media': {'links': {}, 'meta': {}}}

    def _extract_meta_social(self) -> Dict[str, set]:
        """Extrait les informations sociales des méta-tags"""
        meta_social = {}

        try:
            # Meta tags Facebook/Open Graph
            og_tags = self.soup.find_all('meta', attrs={'property': re.compile(r'^og:(title|description|image|url)$')})
            meta_social['og'] = {
                tag.get('content', '') for tag in og_tags
                if tag.get('content')
            }

            # Meta tags Twitter
            twitter_tags = self.soup.find_all('meta', attrs={'name': re.compile(r'^twitter:(card|site|creator|title|description|image)$')})
            meta_social['twitter'] = {
                tag.get('content', '') for tag in twitter_tags
                if tag.get('content')
            }

        except Exception as e:
            print(f"Meta social extraction error: {str(e)}")
            meta_social = {'og': set(), 'twitter': set()}

        return meta_social