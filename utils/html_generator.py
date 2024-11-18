# utils/html_generator.py
from typing import Dict
from datetime import datetime
from urllib.parse import urlparse
from core.analyzer import AnalysisResult


class HTMLReportGenerator:
    @staticmethod
    def generate(results: Dict[str, AnalysisResult]) -> str:
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
            .section {
                background: white;
                padding: 20px;
                margin: 15px 0;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .tech-badge {
                background: #3498db;
                color: white;
                padding: 5px 10px;
                border-radius: 15px;
                margin: 3px;
                display: inline-block;
            }
            .data-table {
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }
            .data-table th, .data-table td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            .email-item, .phone-item {
                background: #f8f9fa;
                padding: 10px;
                margin: 5px 0;
                border-radius: 5px;
            }
        </style>
        """

        html = f"""
        <html>
        <head>
            <title>RhinoScraper Report</title>
            {css}
        </head>
        <body>
            <div class="header">
                <h1>RhinoScraper Analysis Report</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """

        for url, data in results.items():
            domain = urlparse(url).netloc
            html += f"""
            <div class="section">
                <h2>Analysis Results for {domain}</h2>
                <p>URL: {url}</p>
                <p>Status: {data.status_code}</p>
                <p>Analyzed at: {data.analyzed_at}</p>
            </div>
            """

            # Technologies Section
            if data.technologies:
                html += """
                <div class="section">
                    <h3>Technologies Detected</h3>
                """
                for tech in data.technologies:
                    html += f'<span class="tech-badge">{tech}</span>'
                html += "</div>"

            # Security Section
            if data.security:
                html += """
                <div class="section">
                    <h3>Security Information</h3>
                    <table class="data-table">
                """
                for key, value in data.security.items():
                    html += f"<tr><th>{key}</th><td>{value}</td></tr>"
                html += "</table></div>"

            # Contact Information Section
            html += '<div class="section"><h3>Contact Information</h3>'

            if data.emails:
                html += "<h4>Email Addresses</h4>"
                for email in data.emails:
                    html += f"""
                    <div class="email-item">
                        <p>Email: {email.get('email', '')}</p>
                        <p>Domain: {email.get('domain', '')}</p>
                    </div>
                    """

            if data.phones:
                html += "<h4>Phone Numbers</h4>"
                for phone in data.phones:
                    html += f'<div class="phone-item">{phone}</div>'

            html += "</div>"

            # Content Section
            if data.content:
                html += """
                <div class="section">
                    <h3>Page Content Analysis</h3>
                """
                if meta_tags := data.content.get('meta_tags', []):
                    html += "<h4>Meta Tags</h4>"
                    for tag in meta_tags:
                        html += f'<div class="meta-tag">{tag}</div>'
                html += "</div>"

            # Internal Links Section
            if data.internal_links:
                html += """
                <div class="section">
                    <h3>Internal Links Analysis</h3>
                    <table class="data-table">
                        <tr>
                            <th>URL</th>
                            <th>Status</th>
                        </tr>
                """
                for link_url, link_data in data.internal_links.items():
                    if link_data:  # Vérification que link_data n'est pas None
                        html += f"""
                        <tr>
                            <td>{link_url}</td>
                            <td>{link_data.status_code}</td>
                        </tr>
                        """
                html += "</table></div>"

        html += """
            <div class="footer">
                <p>Generated by RhinoScraper - © 2024</p>
            </div>
        </body>
        </html>
        """

        return html

    @staticmethod
    def save_report(html: str, url: str) -> str:
        """Sauvegarde le rapport HTML dans un fichier"""
        filename = f"rhinoscraper_report_{urlparse(url).netloc}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            return filename
        except Exception as e:
            print(f"Error saving report: {str(e)}")
            return None