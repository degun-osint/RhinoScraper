import requests
from bs4 import BeautifulSoup, Comment
import re
from urllib.parse import urljoin, urlparse
from collections import defaultdict
from colorama import init, Fore, Style

init(autoreset=True)

ASCII_ART = """
▗▄▄▖ ▐▌   ▄ ▄▄▄▄   ▄▄▄   ▗▄▄▖▗▞▀▘ ▄▄▄ ▗▞▀▜▌▄▄▄▄  ▗▞▀▚▖ ▄▄▄ 
▐▌ ▐▌▐▌   ▄ █   █ █   █ ▐▌   ▝▚▄▖█    ▝▚▄▟▌█   █ ▐▛▀▀▘█    
▐▛▀▚▖▐▛▀▚▖█ █   █ ▀▄▄▄▀  ▝▀▚▖    █         █▄▄▄▀ ▝▚▄▄▖█    
▐▌ ▐▌▐▌ ▐▌█             ▗▄▄▞▘              █               
                                           ▀               
"""


def extract_info(url, depth=0, max_depth=2):
    if depth > max_depth:
        return {}

    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        comments = soup.find_all(string=lambda string: isinstance(string, Comment))
        google_tags = soup.find_all('meta', attrs={'name': re.compile(r'google-')})

        ga_patterns = [
            r'UA-\d+-\d+',
            r'G-[A-Z0-9]+',
            r"ga\('create',\s*'([^']+)'",
        ]
        ga_codes = []
        for pattern in ga_patterns:
            ga_codes.extend(re.findall(pattern, response.text))

        # Capture meta tag content
        meta_tags = []
        for tag in soup.find_all('meta'):
            name = tag.get('name', '').lower()
            property = tag.get('property', '').lower()
            content = tag.get('content', '')

            if name in ['author', 'creator', 'contributor', 'publisher', 'user'] or \
                    property in ['article:author', 'profile:username', 'og:author']:
                meta_tags.append(content)

        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', response.text)
        internal_links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)
                          if a['href'].startswith('/') or url in a['href']]

        result = {
            'url': url,
            'comments': [str(c) for c in comments],
            'google_tags': [str(t) for t in google_tags] + ga_codes,
            'meta_tags': meta_tags,
            'emails': emails,
            'internal_links': {}
        }

        if depth < max_depth:
            for link in internal_links[:5]:
                result['internal_links'][link] = extract_info(link, depth + 1, max_depth)

        return result
    except Exception as e:
        print(f"{Fore.RED}Error while analyzing {url}: {e}{Style.RESET_ALL}")
        return {}


def consolidate_results(data):
    consolidated = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

    def process_page(url, page_data):
        domain = urlparse(url).netloc
        for key in ['comments', 'google_tags', 'meta_tags', 'emails']:
            for item in page_data[key]:
                consolidated[domain][key][item].add(url)
        for link, link_data in page_data['internal_links'].items():
            process_page(link, link_data)

    process_page(data['url'], data)
    return consolidated


def display_results(consolidated):
    for domain, data in consolidated.items():
        print(f"\n{Fore.CYAN}Results for domain: {domain}{Style.RESET_ALL}")
        for key, items in data.items():
            print(f"{Fore.GREEN}{key.capitalize()}: {len(items)} unique{Style.RESET_ALL}")
            if key == 'meta_tags':
                for item in items:
                    print(f"  - {item}")


def generate_html(consolidated):
    css = """
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        h2 { color: #2980b9; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #3498db; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .pages { font-size: 0.9em; color: #7f8c8d; }
        pre { background-color: #f8f8f8; border: 1px solid #ddd; padding: 15px; white-space: pre-wrap; word-wrap: break-word; }
    </style>
    """

    html = f"<html><head>{css}</head><body>"
    html += f"<pre>{ASCII_ART}</pre>"

    for domain, data in consolidated.items():
        html += f"<h1>Results for domain: {domain}</h1>"

        for key in ['comments', 'google_tags', 'meta_tags', 'emails']:
            items = data.get(key, {})
            html += f"<h2>{key.capitalize()} ({len(items)} unique)</h2>"
            html += "<table><tr><th>Content</th><th>Pages</th></tr>"

            if not items:
                html += "<tr><td colspan='2'>No data available</td></tr>"
            else:
                for item, pages in items.items():
                    pages_str = ", ".join(sorted(pages))
                    html += f"<tr><td>{item}</td><td class='pages'>{pages_str}</td></tr>"

            html += "</table>"

    html += "</body></html>"
    return html


def main():
    print(f"{Fore.CYAN}{ASCII_ART}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Welcome to RhinoScraper{Style.RESET_ALL}")
    urls_input = input("Enter one or more URLs to analyze (comma-separated): ")
    urls = [url.strip() for url in urls_input.split(',')]

    while True:
        depth_input = input("Enter the depth level for link analysis (a positive integer): ")
        try:
            max_depth = int(depth_input)
            if max_depth < 1:
                raise ValueError
            break
        except ValueError:
            print(f"{Fore.RED}Please enter a valid positive integer.{Style.RESET_ALL}")

    all_results = {}
    for url in urls:
        print(f"\n{Fore.YELLOW}Analyzing {url} (depth: {max_depth})...{Style.RESET_ALL}")
        result = extract_info(url, max_depth=max_depth)
        consolidated = consolidate_results(result)
        all_results.update(consolidated)
        display_results(consolidated)

    save_option = input("\nDo you want to save the results? (Enter a filename or 'no' to quit): ")
    if save_option.lower() != 'no':
        with open(f"{save_option}.html", "w", encoding="utf-8") as f:
            f.write(generate_html(all_results))
        print(f"{Fore.GREEN}Results saved in {save_option}.html{Style.RESET_ALL}")

    print(f"{Fore.CYAN}Thank you for using the Web Analyzer!{Style.RESET_ALL}")


if __name__ == "__main__":
    main()