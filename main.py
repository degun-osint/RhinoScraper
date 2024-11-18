import asyncio
import sys
from colorama import init, Fore, Style
from core.analyzer import SiteAnalyzer
from core.session import SessionManager
from core.cache import RhinoCache
from utils.html_generator import HTMLReportGenerator
from config.settings import Settings

init(autoreset=True)

ASCII_ART = """
▗▄▄▖ ▐▌   ▄ ▄▄▄▄   ▄▄▄   ▗▄▄▖▗▞▀▘ ▄▄▄ ▗▞▀▜▌▄▄▄▄  ▗▞▀▚▖ ▄▄▄ 
▐▌ ▐▌▐▌   ▄ █   █ █   █ ▐▌   ▝▚▄▖█    ▝▚▄▟▌█   █ ▐▛▀▀▘█    
▐▛▀▚▖▐▛▀▚▖█ █   █ ▀▄▄▄▀  ▝▀▚▖    █         █▄▄▄▀ ▝▚▄▄▖█    
▐▌ ▐▌▐▌ ▐▌█             ▗▄▄▞▘              █               
                                           ▀               
"""


async def main():
    print(f"{Fore.CYAN}{ASCII_ART}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Welcome to RhinoScraper - Advanced OSINT Tool{Style.RESET_ALL}")

    try:
        url = input("Enter URL to analyze: ")
        settings = Settings.get_instance()  # Utilisation des settings

        max_depth = int(input(f"Enter maximum depth (1-{settings.MAX_DEPTH}): "))
        if not (1 <= max_depth <= settings.MAX_DEPTH):
            raise ValueError(f"Depth must be between 1 and {settings.MAX_DEPTH}")

        session_manager = SessionManager()
        cache = RhinoCache()
        analyzer = SiteAnalyzer(session_manager, cache)

        print(f"\n{Fore.YELLOW}Starting analysis of {url}...{Style.RESET_ALL}")

        try:
            result = await analyzer.analyze(url, depth=0)
            html_report = HTMLReportGenerator.generate({url: result})
            filename = HTMLReportGenerator.save_report(html_report, url)

            print(f"\n{Fore.GREEN}Analysis complete! Report saved as {filename}{Style.RESET_ALL}")

        finally:
            await session_manager.close()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Analysis interrupted by user.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}Error during analysis: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())