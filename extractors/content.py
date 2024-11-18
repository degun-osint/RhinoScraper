from typing import Dict, List, Any
import re
from bs4 import BeautifulSoup, Comment
from .base import BaseExtractor


class ContentExtractor(BaseExtractor):
    async def extract(self) -> Dict[str, Any]:
        try:
            meta_tags = []
            for tag in self.soup.find_all('meta'):
                name = tag.get('name', '')
                property = tag.get('property', '')
                content = tag.get('content', '')
                if content and (name or property):
                    meta_tags.append(f"{name or property}: {content}")

            google_tags = []
            for tag in self.soup.find_all('meta'):
                if tag.get('name', '').startswith('google-'):
                    google_tags.append(str(tag))

            return {
                'content': {
                    'meta_tags': meta_tags,
                    'comments': [str(c) for c in self.soup.find_all(
                        string=lambda text: isinstance(text, Comment)
                    )],
                    'google_tags': google_tags,
                    'dates': re.findall(r'\d{4}-\d{2}-\d{2}', str(self.soup))
                }
            }
        except Exception as e:
            print(f"Content extraction error: {str(e)}")
            return {'content': {}}

    def _extract_meta_tags(self) -> List[str]:
        meta_tags = []
        for tag in self.soup.find_all('meta'):
            name = tag.get('name', '').lower()
            property = tag.get('property', '').lower()
            content = tag.get('content', '')
            if content and (name in ['description', 'keywords', 'author'] or
                          property.startswith('og:')):
                meta_tags.append(f"{name or property}: {content}")
        return meta_tags

    def _extract_comments(self) -> List[str]:
        return [str(c) for c in self.soup.find_all(
            string=lambda text: isinstance(text, Comment)
        )]

    def _extract_google_tags(self) -> List[str]:
        google_tags = []
        google_tags.extend([
            str(t) for t in self.soup.find_all('meta',
            attrs={'name': re.compile(r'google-')})
        ])
        google_tags.extend(
            re.findall(r'UA-\d+-\d+|G-[A-Z0-9]+', str(self.soup))
        )
        return google_tags

    def _extract_dates(self) -> List[str]:
        return re.findall(r'\d{4}-\d{2}-\d{2}', str(self.soup))