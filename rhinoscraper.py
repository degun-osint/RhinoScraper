import requests
from bs4 import BeautifulSoup, Comment
import re
import socket
import whois
from urllib.parse import urljoin, urlparse
from collections import defaultdict
from colorama import init, Fore, Style
import ssl
import phonenumbers
from concurrent.futures import ThreadPoolExecutor
from email_validator import validate_email, EmailNotValidError
from diskcache import Cache
from datetime import datetime, timedelta
import validators

init(autoreset=True)

ASCII_ART = """
▗▄▄▖ ▐▌   ▄ ▄▄▄▄   ▄▄▄   ▗▄▄▖▗▞▀▘ ▄▄▄ ▗▞▀▜▌▄▄▄▄  ▗▞▀▚▖ ▄▄▄ 
▐▌ ▐▌▐▌   ▄ █   █ █   █ ▐▌   ▝▚▄▖█    ▝▚▄▟▌█   █ ▐▛▀▀▘█    
▐▛▀▚▖▐▛▀▚▖█ █   █ ▀▄▄▄▀  ▝▀▚▖    █         █▄▄▄▀ ▝▚▄▄▖█    
▐▌ ▐▌▐▌ ▐▌█             ▗▄▄▞▘              █               
                                           ▀               
"""


def check_sensitive_files(base_url):
    """
    Vérifie la présence de fichiers et répertoires sensibles.
    """
    sensitive_paths = [
        'robots.txt',
        '.git/HEAD',
        '.env',
        'wp-config.php',
        '.htaccess',
        '.htpasswd',
        'config.php',
        'sitemap.xml',
        'administrator/',
        'admin/',
        '.DS_Store',
        'backup/',
        'phpinfo.php',
        '.svn/',
        'credentials.txt',
        '.bash_history',
        'backup.sql',
        'debug.log'
    ]

    exposed_files = []

    for path in sensitive_paths:
        try:
            url = f"{base_url.rstrip('/')}/{path}"
            response = requests.head(url, allow_redirects=False, timeout=5)

            if response.status_code in [200, 403]:  # 403 peut aussi être intéressant car il confirme l'existence
                exposed_files.append({
                    'path': path,
                    'status': response.status_code,
                    'url': url,
                    'risk_level': 'HIGH' if '.env' in path or 'config' in path else 'MEDIUM'
                })
        except:
            continue

    return exposed_files


def extract_emails(text):
    """
    Extrait et valide les adresses email du texte.
    """
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    potential_emails = re.findall(email_pattern, text)

    validated_emails = []
    for email in set(potential_emails):  # Utilisation d'un set pour dédupliquer
        try:
            valid = validate_email(email)
            validated_emails.append({
                'email': valid.email,
                'domain': valid.domain,
                'source': 'page_content'
            })
        except EmailNotValidError:
            continue

    return validated_emails


class RhinoCache:
    """
    Gestion du cache pour éviter de rescraper les mêmes pages.
    """

    def __init__(self, cache_dir='./rhinocache', expiration_days=7):
        self.cache = Cache(cache_dir)
        self.expiration = timedelta(days=expiration_days)

    def get_cache_key(self, url):
        return f"rhino_{url}"

    def get(self, url):
        key = self.get_cache_key(url)
        cached_data = self.cache.get(key)

        if cached_data:
            cached_time = cached_data.get('timestamp')
            if cached_time and datetime.now() - datetime.fromisoformat(cached_time) < self.expiration:
                return cached_data.get('data')
        return None

    def set(self, url, data):
        key = self.get_cache_key(url)
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        self.cache.set(key, cache_data, expire=int(self.expiration.total_seconds()))

    def clear(self):
        self.cache.clear()

def get_ssl_info(hostname):
    try:
        context = ssl.create_default_context()
        with context.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.connect((hostname, 443))
            cert = s.getpeercert()
            return {
                'issuer': dict(x[0] for x in cert['issuer']),
                'expiry': cert['notAfter'],
                'subject': dict(x[0] for x in cert['subject']),
            }
    except Exception as e:
        return f"SSL Error: {str(e)}"


def detect_technologies(soup, headers):
    technologies = []

    # CMS Detection
    if soup.find(attrs={"name": "generator"}):
        technologies.append(f"CMS: {soup.find(attrs={'name': 'generator'})['content']}")

    # Common frameworks
    if soup.find(attrs={"name": "viewport"}):
        technologies.append("Responsive Design")
    if "wp-content" in str(soup):
        technologies.append("WordPress")
    if "drupal" in str(soup).lower():
        technologies.append("Drupal")

    # Server info
    if 'Server' in headers:
        technologies.append(f"Server: {headers['Server']}")

    # Security headers
    security_headers = {
        'Strict-Transport-Security': 'HSTS',
        'Content-Security-Policy': 'CSP',
        'X-Frame-Options': 'X-Frame-Options',
        'X-XSS-Protection': 'XSS Protection'
    }

    for header, name in security_headers.items():
        if header in headers:
            technologies.append(f"Security: {name}")

    return technologies


def extract_social_media(soup):
    social_patterns = {
        'facebook': r'facebook.com/[\w\.]+',
        'twitter': r'twitter.com/[\w\.]+',
        'linkedin': r'linkedin.com/[\w\-]+',
        'instagram': r'instagram.com/[\w\.]+',
        'youtube': r'youtube.com/[\w\-]+',
    }

    social_links = defaultdict(set)

    for platform, pattern in social_patterns.items():
        links = re.findall(pattern, str(soup))
        social_links[platform].update(links)

    return dict(social_links)


def extract_phones(text):
    all_phones = set()  # Utilisation d'un set pour éviter les doublons

    # Liste des codes pays les plus courants
    country_codes = [
        "US", "GB", "FR", "DE", "ES", "IT", "CH", "BE", "NL",
        "CA", "AU", "IN", "CN", "JP", "BR", "RU", "AE", "SA",
        # On peut ajouter d'autres codes pays si nécessaire
    ]

    # Recherche pour chaque code pays
    for region in country_codes:
        try:
            for match in phonenumbers.PhoneNumberMatcher(text, region):
                # Formatage du numéro en format international
                formatted_number = phonenumbers.format_number(
                    match.number,
                    phonenumbers.PhoneNumberFormat.INTERNATIONAL
                )
                all_phones.add(formatted_number)
        except Exception:
            continue

    # Recherche de motifs génériques de numéros de téléphone
    # Motifs additionnels pour attraper les numéros qui ne suivent pas les formats standards
    generic_patterns = [
        r'\+\d{1,4}[-\s]?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{1,4}',  # Format international
        r'\(\d{1,4}\)[-\s]?\d{1,4}[-\s]?\d{1,4}',  # Format avec parenthèses
        r'\d{2,4}[-\s.]\d{2,4}[-\s.]\d{2,4}',  # Format séparé par tirets ou points
    ]

    for pattern in generic_patterns:
        potential_numbers = re.findall(pattern, text)
        for num in potential_numbers:
            # Nettoyage basique
            cleaned = re.sub(r'[\s\(\)-.]', '', num)
            if len(cleaned) >= 8:  # Longueur minimale pour un numéro valide
                all_phones.add(num.strip())

    return list(all_phones)

def get_domain_info(domain):
    try:
        w = whois.whois(domain)
        return {
            'registrar': w.registrar,
            'creation_date': w.creation_date,
            'expiration_date': w.expiration_date,
            'name_servers': w.name_servers,
        }
    except Exception as e:
        return f"WHOIS Error: {str(e)}"


def extract_info(url, depth=0, max_depth=2, cache=None):
    if cache:
        cached_result = cache.get(url)
        if cached_result:
            return cached_result

    try:
        base_domain = urlparse(url).netloc
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # HTML Comments
        comments = soup.find_all(string=lambda string: isinstance(string, Comment))

        # Google Tags & Analytics
        google_tags = soup.find_all('meta', attrs={'name': re.compile(r'google-')})
        ga_patterns = [
            r'UA-\d+-\d+',
            r'G-[A-Z0-9]+',
            r"ga\('create',\s*'([^']+)'",
        ]
        ga_codes = []
        for pattern in ga_patterns:
            ga_codes.extend(re.findall(pattern, response.text))

        meta_tags = []
        for tag in soup.find_all('meta'):
            name = tag.get('name', '').lower()
            property = tag.get('property', '').lower()
            content = tag.get('content', '')

            if content and (
                    name in ['author', 'creator', 'contributor', 'publisher', 'user', 'description', 'keywords'] or
                    property in ['article:author', 'profile:username', 'og:author', 'og:description']
            ):
                # Ajouter le type de meta tag pour plus de clarté
                prefix = name if name else property
                meta_tags.append(f"{prefix}: {content}")

        # Get visible text for name extraction
        visible_text = ' '.join([text for text in soup.stripped_strings])

        # Extractions
        technologies = detect_technologies(soup, response.headers)
        social_links = extract_social_media(soup)
        phones = extract_phones(response.text)
        ssl_info = get_ssl_info(base_domain)
        domain_info = get_domain_info(base_domain)
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', response.text)

        result = {
            'url': url,
            'comments': [str(c) for c in comments],
            'google_tags': [str(t) for t in google_tags] + ga_codes,
            'meta_tags': meta_tags,
            'technologies': technologies,
            'social_media': social_links,
            'phones': phones,
            'ssl_info': ssl_info,
            'domain_info': domain_info,
            'sensitive_files': check_sensitive_files(url),
            'emails': extract_emails(response.text),
            'dates': dates,
            'response_headers': dict(response.headers),
            'status_code': response.status_code,
            'internal_links': {}
        }

        if depth < max_depth:
            internal_links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                # Ignorer les liens non-HTTP
                if not href.startswith(('mailto:', 'tel:', 'javascript:', '#', 'whatsapp:')):
                    try:
                        full_url = urljoin(url, href)
                        parsed_url = urlparse(full_url)
                        # Vérifier que le domaine est exactement le même
                        if parsed_url.netloc == base_domain:
                            internal_links.append(full_url)
                    except:
                        continue

            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_url = {executor.submit(extract_info, link, depth + 1, max_depth): link
                                for link in internal_links[:5]}
                for future in future_to_url:
                    link = future_to_url[future]
                    try:
                        result['internal_links'][link] = future.result()
                    except Exception as e:
                        print(f"{Fore.YELLOW}Error analyzing {link}: {e}{Style.RESET_ALL}")

        if cache:
            cache.set(url, result)

        return result
    except Exception as e:
        print(f"{Fore.RED}Error while analyzing {url}: {e}{Style.RESET_ALL}")
        return {}


def generate_html(results):
    css = """
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f6fa;
        }
        .header {
            text-align: center;
            padding: 20px;
            background: #2c3e50;
            color: white;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header pre {
            color: #3498db;
            margin: 0;
            font-family: monospace;
        }
        h1 { 
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-top: 40px;
        }
        h2 { color: #2980b9; }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-2px);
        }
        .card h3 {
            margin-top: 0;
            color: #2980b9;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 10px;
        }
        .tech-badge {
            background: #3498db;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            margin: 3px;
            display: inline-block;
            font-size: 0.9em;
        }
        .security-info {
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #2ecc71;
            border-radius: 5px;
        }
        .warning {
            background: #fff3cd;
            padding: 15px;
            border-left: 4px solid #ffc107;
            border-radius: 5px;
        }
        
        .name-category {
            font-weight: bold;
            color: #2c3e50;
            margin: 15px 0 10px 0;
        }

        .comments, .google-analytics {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            font-family: monospace;
            overflow-x: auto;
        }
        .footer {
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            color: #7f8c8d;
        }
        .meta-tag {
            background: #34495e;
            color: #ecf0f1;
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
            font-family: monospace;
            overflow-x: auto;
        }
        .sensitive-file {
        background: #fff3cd;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
    .high-risk {
        border-left: 4px solid #dc3545;
    }
    .email-item {
        background: #e9ecef;
        padding: 8px;
        margin: 3px 0;
        border-radius: 4px;
        font-family: monospace;
    }
    </style>
    """

    html = f"<html><head>{css}</head><body>"

    # Header with ASCII Art
    html += """
    <div class="header">
        <pre>
▗▄▄▖ ▐▌   ▄ ▄▄▄▄   ▄▄▄   ▗▄▄▖▗▞▀▘ ▄▄▄ ▗▞▀▜▌▄▄▄▄  ▗▞▀▚▖ ▄▄▄ 
▐▌ ▐▌▐▌   ▄ █   █ █   █ ▐▌   ▝▚▄▖█    ▝▚▄▟▌█   █ ▐▛▀▀▘█    
▐▛▀▚▖▐▛▀▚▖█ █   █ ▀▄▄▄▀  ▝▀▚▖    █         █▄▄▄▀ ▝▚▄▄▖█    
▐▌ ▐▌▐▌ ▐▌█             ▗▄▄▞▘              █               
                                           ▀               
        </pre>
        <h1 style="color: white; border: none;">RhinoScraper Report</h1>
    </div>
    """

    for url, data in results.items():
        domain = urlparse(url).netloc
        html += f"<h1>Analysis Results for {domain}</h1>"

        # HTML Comments Section
        if data.get('comments'):
            html += '<div class="card">'
            html += "<h3>HTML Comments</h3>"
            for comment in data.get('comments', []):
                html += f'<div class="comments"><code>{comment}</code></div>'
            html += "</div>"

        # Google Analytics Section
        if data.get('google_tags'):
            html += '<div class="card">'
            html += "<h3>Google Analytics & Tags</h3>"
            for tag in data.get('google_tags', []):
                html += f'<div class="google-analytics"><code>{tag}</code></div>'
            html += "</div>"

        # Meta
        if data.get('meta_tags'):
            html += '<div class="card">'
            html += "<h3>Meta Tags</h3>"
            for tag in data.get('meta_tags', []):
                if tag.strip():  # Vérifier que le tag n'est pas vide
                    html += f'<div class="meta-tag"><code>{tag}</code></div>'
            html += "</div>"

        # Technologies Section
        html += '<div class="card">'
        html += "<h3>Technologies Detected</h3>"
        for tech in data.get('technologies', []):
            html += f'<span class="tech-badge">{tech}</span>'
        html += "</div>"

        # Security Section
        html += '<div class="card">'
        html += "<h3>Security Information</h3>"
        html += '<div class="security-info">'
        ssl_info = data.get('ssl_info', {})
        if isinstance(ssl_info, dict):
            html += f"<p>SSL Issuer: {ssl_info.get('issuer', {}).get('organizationName', 'N/A')}</p>"
            html += f"<p>SSL Expiry: {ssl_info.get('expiry', 'N/A')}</p>"
        html += "</div></div>"

        # Contact Information
        html += '<div class="card">'
        html += "<h3>Contact Information</h3>"
        html += "<h4>Phone Numbers</h4>"
        for phone in data.get('phones', []):
            html += f"<p>{phone}</p>"
        html += "<h4>Social Media</h4>"
        for platform, links in data.get('social_media', {}).items():
            html += f"<p>{platform.title()}: {', '.join(links)}</p>"
        html += "</div>"

        # Domain Information
        html += '<div class="card">'
        html += "<h3>Domain Information</h3>"
        domain_info = data.get('domain_info', {})
        if isinstance(domain_info, dict):
            html += f"<p>Registrar: {domain_info.get('registrar', 'N/A')}</p>"
            html += f"<p>Creation Date: {domain_info.get('creation_date', 'N/A')}</p>"
            html += f"<p>Expiration Date: {domain_info.get('expiration_date', 'N/A')}</p>"
        html += "</div>"

        # Sensitive Files Section
        html += '<div class="card">'
        html += "<h3>Exposed Sensitive Files</h3>"
        for file in data.get('sensitive_files', []):
            html += f'''
                <div class="sensitive-file {'high-risk' if file['risk_level'] == 'HIGH' else ''}">
                    <strong>{file['path']}</strong> (Status: {file['status']})
                    <br>
                    <small>Risk Level: {file['risk_level']}</small>
                </div>
                '''
        html += "</div>"

        # Emails Section
        html += '<div class="card">'
        html += "<h3>Detected Email Addresses</h3>"
        for email in data.get('emails', []):
            html += f'''
                <div class="email-item">
                    📧 {email['email']} <small>({email['domain']})</small>
                </div>
                '''
        html += "</div>"


    # Footer
    html += """
    <div class="footer">
        <p>Generated by RhinoScraper - Advanced OSINT Tool</p>
        <p>🦏</p>
    </div>
    """

    html += "</body></html>"
    return html


def main():
    print(f"{Fore.CYAN}{ASCII_ART}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Welcome to RhinoScraper - Advanced OSINT Tool{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Version: 2.0 - Enhanced Edition{Style.RESET_ALL}")

    url = input("Enter URL to analyze: ")
    while True:
        try:
            max_depth = int(input("Enter maximum depth for analysis (1-3): "))
            if 1 <= max_depth <= 3:
                break
            print(f"{Fore.RED}Please enter a number between 1 and 3{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number{Style.RESET_ALL}")

    print(f"\n{Fore.YELLOW}🦏 RhinoScraper starting analysis of {url}...{Style.RESET_ALL}")

    cache = RhinoCache()
    results = {url: extract_info(url, max_depth=max_depth, cache=cache)}

    filename = f"rhinoscraper_report_{urlparse(url).netloc}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(generate_html(results))

    print(f"{Fore.GREEN}🦏 RhinoScraper analysis complete! Report saved as {filename}{Style.RESET_ALL}")

    # Affichage du résumé
    print(f"\n{Fore.CYAN}Quick Summary:{Style.RESET_ALL}")
    domain = urlparse(url).netloc
    tech_count = len(results[url].get('technologies', []))
    phone_count = len(results[url].get('phones', []))
    social_count = sum(len(links) for links in results[url].get('social_media', {}).values())

    print(f"- Technologies detected: {tech_count}")
    print(f"- Phone numbers found: {phone_count}")
    print(f"- Social media links: {social_count}")
    print(f"- Meta tags found: {len(results[url].get('meta_tags', []))}")



if __name__ == "__main__":
    main()