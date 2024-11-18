from typing import Dict, List, Any
import re
from email_validator import validate_email
from .base import BaseExtractor


class EmailExtractor(BaseExtractor):
    async def extract(self) -> Dict[str, List[Dict[str, str]]]:
        """Extrait et valide les adresses email du contenu"""
        all_emails = set()

        # Pattern email optimisé
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

        # Recherche dans le texte
        all_emails.update(re.findall(email_pattern, str(self.soup)))

        # Recherche dans les liens mailto
        for link in self.soup.find_all('a', href=lambda x: x and 'mailto:' in x.lower()):
            href = link['href']
            email = href.replace('mailto:', '').split('?')[0].strip()
            if '@' in email:
                all_emails.add(email)

        validated_emails = []
        for email in all_emails:
            try:
                valid = validate_email(email)
                validated_emails.append({
                    'email': valid.email,
                    'domain': valid.domain,
                    'source': 'page_content'
                })
            except:
                continue

        return {'emails': validated_emails}