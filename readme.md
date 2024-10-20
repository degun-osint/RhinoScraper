```
▗▄▄▖ ▐▌   ▄ ▄▄▄▄   ▄▄▄   ▗▄▄▖▗▞▀▘ ▄▄▄ ▗▞▀▜▌▄▄▄▄  ▗▞▀▚▖ ▄▄▄ 
▐▌ ▐▌▐▌   ▄ █   █ █   █ ▐▌   ▝▚▄▖█    ▝▚▄▟▌█   █ ▐▛▀▀▘█    
▐▛▀▚▖▐▛▀▚▖█ █   █ ▀▄▄▄▀  ▝▀▚▖    █         █▄▄▄▀ ▝▚▄▄▖█    
▐▌ ▐▌▐▌ ▐▌█             ▗▄▄▞▘              █               
                                           ▀  
```
# RhinoScraper

RhinoScraper is a Python script that analyzes web pages, extracting various types of information and following internal links to a specified depth.

## Features

- Extracts HTML comments
- Detects Google Analytics codes and other Google tags (or not...)
- Finds meta tags related to authors and users
- Extracts email addresses
- Follows internal links to a user-specified depth
- Generates an HTML report with the findings

## Installation

1. Clone this repository or download the script.
2. Install the required packages:

```
pip install -r requirements.txt
```

## Usage

Run the script with Python:

```
python web_analyzer.py
```

Follow the prompts to enter:
1. One or more URLs to analyze (comma-separated)
2. The depth level for link analysis

The script will display a summary of the results in the console and offer to save a detailed HTML report.

## Output

The script generates an HTML report with tables for each type of extracted information:
- Comments
- Google tags (including Analytics codes)
- Meta tags
- Email addresses

Each table shows the unique items found and the pages where they were located.

## Note

This script is for educational purposes only. Always respect website terms of service and robots.txt files when scraping websites.

## License

This project is open source and available under the MIT License.