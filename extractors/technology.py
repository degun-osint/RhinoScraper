import re
from typing import Dict, List, Any
from .base import BaseExtractor

class TechnologyExtractor(BaseExtractor):
    async def extract(self) -> Dict[str, Any]:
        """Détecte les technologies utilisées sur le site"""
        technologies = set()

        # Patterns de détection rapide
        tech_patterns = {
            'wordpress': 'WordPress',
            'drupal': 'Drupal',
            'joomla': 'Joomla',
            'bootstrap': 'Bootstrap',
            'jquery': 'jQuery',
            'react': 'React',
            'vue': 'Vue.js',
            'angular': 'Angular'
        }

        html_content = str(self.soup).lower()
        for pattern, tech_name in tech_patterns.items():
            if pattern in html_content:
                technologies.add(tech_name)

        # Détection CMS
        if generator := self.soup.find('meta', attrs={'name': 'generator'}):
            technologies.add(f"CMS: {generator.get('content', '')}")

        # Frameworks responsives
        if self.soup.find('meta', attrs={'name': 'viewport'}):
            technologies.add("Responsive Design")

        return {'technologies': sorted(list(technologies))}