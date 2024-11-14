# 🦏 RhinoScraper

RhinoScraper is an advanced OSINT (Open Source Intelligence) tool designed to analyze websites and extract various types of information, including security data, contact details, technologies used, and legal information.

```
▗▄▄▖ ▐▌   ▄ ▄▄▄▄   ▄▄▄   ▗▄▄▖▗▞▀▘ ▄▄▄ ▗▞▀▜▌▄▄▄▄  ▗▞▀▚▖ ▄▄▄ 
▐▌ ▐▌▐▌   ▄ █   █ █   █ ▐▌   ▝▚▄▖█    ▝▚▄▟▌█   █ ▐▛▀▀▘█    
▐▛▀▚▖▐▛▀▚▖█ █   █ ▀▄▄▄▀  ▝▀▚▖    █         █▄▄▄▀ ▝▚▄▄▖█    
▐▌ ▐▌▐▌ ▐▌█             ▗▄▄▞▘              █               
                                           ▀               
```

## Features

RhinoScraper can extract and analyze:

- **Security Information**
  - SSL certificate details
  - Security headers
  - Exposed sensitive files
  - robots.txt content

- **Technology Detection**
  - CMS identification
  - Web frameworks
  - Server technology
  - Security implementations

- **Contact Information**
  - Email addresses (with validation)
  - Phone numbers (international format)
  - Social media links

- **Technical Data**
  - HTML comments
  - Meta tags
  - Google Analytics codes
  - Domain information (WHOIS)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/degun-osint/rhinoscraper.git
cd rhinoscraper
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

## Dependencies

- beautifulsoup4
- requests
- python-whois
- colorama
- phonenumbers
- email-validator
- diskcache
- validators

## Usage

Run the script:
```bash
python rhinoscraper.py
```

The tool will prompt you for:
1. The URL to analyze
2. The maximum depth for crawling (1-3)

## Output

RhinoScraper generates an HTML report containing:

- Comprehensive analysis results
- Color-coded risk assessments
- Interactive elements
- Clean, modern design
- Mobile-friendly layout

Reports are saved as HTML files with the following naming convention:
```
rhinoscraper_report_[domain]_[timestamp].html
```

## Caching

The tool implements a caching system to:
- Avoid redundant scraping
- Improve performance
- Reduce server load
- Store results for 7 days (configurable)

## Features in Detail

### Sensitive File Detection
Checks for commonly exposed sensitive files and directories:
- .git
- .env
- wp-config.php
- and more...

### Email Validation
- Extracts potential email addresses
- Validates format and structure
- Removes duplicates
- Identifies domains

### Social Media Detection
Identifies profiles on:
- Facebook
- Twitter
- LinkedIn
- Instagram
- YouTube

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Security

- RhinoScraper is designed for legal and ethical use only
- Always obtain permission before scanning non-public websites
- Be mindful of rate limiting and server load
- Follow responsible disclosure practices for any security findings

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Users are responsible for complying with applicable laws and regulations. The authors are not responsible for any misuse or damage caused by this program.

## Author

Degun

## Acknowledgments

- Beautiful Soup documentation
- Python Requests library
- OSINT community