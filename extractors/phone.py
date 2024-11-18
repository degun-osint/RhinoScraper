import phonenumbers
from typing import Dict, List, Any
import re
from .base import BaseExtractor


class PhoneExtractor(BaseExtractor):
    def __init__(self, soup, url):
        super().__init__(soup, url)
        self.country_codes = [
            "US", "GB", "FR", "DE", "ES", "IT", "CH", "BE", "NL",
            "CA", "AU", "IN", "CN", "JP", "BR", "RU"
        ]

    def is_valid_phone(self, phone_obj: phonenumbers.PhoneNumber) -> bool:
        """
        Vérifie si un numéro de téléphone est valide selon des critères stricts
        """
        # Vérifier si le numéro est valide selon la lib phonenumbers
        if not phonenumbers.is_valid_number(phone_obj):
            return False

        # Obtenir les informations sur le numéro
        number_type = phonenumbers.number_type(phone_obj)

        # N'accepter que les types de numéros légitimes
        valid_types = [
            phonenumbers.PhoneNumberType.MOBILE,
            phonenumbers.PhoneNumberType.FIXED_LINE,
            phonenumbers.PhoneNumberType.FIXED_LINE_OR_MOBILE
        ]

        if number_type not in valid_types:
            return False

        # Vérifier la longueur minimale (en excluant le code pays et les formatages)
        national_number = str(phone_obj.national_number)
        if len(national_number) < 6:  # La plupart des numéros légitimes ont au moins 6 chiffres
            return False

        return True

    def clean_number(self, number: str) -> str:
        """Nettoie un numéro de téléphone des caractères non désirés"""
        # Supprimer les caractères non numériques tout en gardant le +
        cleaned = re.sub(r'[^\d+]', '', number)

        # S'assurer qu'il n'y a qu'un seul + au début
        if '+' in cleaned[1:]:
            cleaned = cleaned.replace('+', '', 1)

        return cleaned

    def process_generic_match(self, number: str) -> str:
        """
        Traite les correspondances génériques pour éliminer les faux positifs évidents
        """
        # Nettoyer le numéro
        cleaned = self.clean_number(number)

        # Rejeter les numéros qui ne respectent pas les critères de base
        if len(cleaned) < 8:  # Trop court pour être un vrai numéro
            return None

        if cleaned.count('0') / len(cleaned) > 0.5:  # Trop de zéros
            return None

        if re.search(r'(\d)\1{4,}', cleaned):  # Séquence de 5+ chiffres identiques
            return None

        # Rejeter les séquences évidentes
        sequences = ['01234', '12345', '23456', '34567', '45678', '56789']
        if any(seq in cleaned for seq in sequences):
            return None

        # Rejeter les numéros qui sont juste des incréments
        if re.search(r'^(\d)(\d)(\d)(\d)-\1\2\3(\d)$', number):  # Format type 0102-0103
            return None

        return cleaned

    async def extract(self) -> Dict[str, List[str]]:
        """Extrait les numéros de téléphone du contenu avec validation améliorée"""
        text = str(self.soup)
        valid_phones = set()

        # Première passe : utiliser phonenumbers pour les numéros bien formés
        for region in self.country_codes:
            try:
                matches = phonenumbers.PhoneNumberMatcher(text, region)
                for match in matches:
                    if self.is_valid_phone(match.number):
                        formatted = phonenumbers.format_number(
                            match.number,
                            phonenumbers.PhoneNumberFormat.INTERNATIONAL
                        )
                        valid_phones.add(formatted)
            except Exception:
                continue

        # Deuxième passe : patterns génériques avec validation stricte
        generic_patterns = [
            r'\+\d{1,3}[-\s]?\d{1,4}[-\s]?\d{3,4}[-\s]?\d{3,4}',  # Format international
            r'\(\d{2,4}\)[-\s]?\d{3,4}[-\s]?\d{3,4}'  # Format avec parenthèses
        ]

        for pattern in generic_patterns:
            potential_numbers = re.findall(pattern, text)
            for num in potential_numbers:
                cleaned = self.process_generic_match(num)
                if cleaned:
                    # Tenter de parser avec phonenumbers pour validation finale
                    try:
                        phone_obj = phonenumbers.parse(cleaned, None)
                        if self.is_valid_phone(phone_obj):
                            formatted = phonenumbers.format_number(
                                phone_obj,
                                phonenumbers.PhoneNumberFormat.INTERNATIONAL
                            )
                            valid_phones.add(formatted)
                    except Exception:
                        continue

        return {'phones': sorted(list(valid_phones))}