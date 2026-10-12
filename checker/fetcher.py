"""
Fetcher module for downloading and parsing web pages using Requests and BeautifulSoup.
Extracts both clean text paragraphs and formatting indicators (like bold/strong tags).
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def is_valid_url(url: str) -> bool:
    """Validate that the URL has http/https scheme and a valid network location."""
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except Exception:
        return False


def fetch_and_parse_page(url: str, timeout: int = 12) -> dict:
    """
    Fetches the URL and extracts:
      - text: Full normalized clean text content.
      - sentences: List of normalized sentences or paragraphs for evidence matching.
      - bold_texts: List of text strings found inside <b>, <strong>, or bold style elements.
      - links: List of hyperlinks (href and anchor text).
      - title: Webpage title.
      - error: Error message if failed, else None.
    """
    result = {
        "success": False,
        "url": url,
        "status_code": None,
        "title": "",
        "text": "",
        "sentences": [],
        "bold_texts": [],
        "links": [],
        "error": None,
    }

    if not is_valid_url(url):
        result["error"] = "Invalid URL. Please enter a valid URL beginning with http:// or https://"
        return result

    try:
        session = requests.Session()
        response = session.get(url.strip(), headers=DEFAULT_HEADERS, timeout=timeout, allow_redirects=True)
        result["status_code"] = response.status_code

        if response.status_code >= 400:
            result["error"] = f"HTTP Error {response.status_code}: Unable to access webpage."
            return result

        # Parse HTML
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract title
        if soup.title and soup.title.string:
            result["title"] = soup.title.string.strip()

        # Extract bold texts before stripping tags (important for STOP/HELP bold detection)
        bold_elements = soup.find_all(['b', 'strong'])
        for el in bold_elements:
            t = el.get_text(strip=True)
            if t:
                result["bold_texts"].append(t)

        # Also search elements with inline style containing font-weight: bold or 700+
        for el in soup.find_all(attrs={"style": re.compile(r"font-weight\s*:\s*(bold|[6-9]00)", re.IGNORECASE)}):
            t = el.get_text(strip=True)
            if t and t not in result["bold_texts"]:
                result["bold_texts"].append(t)

        # Extract all links (for detecting privacy policy link in TOS)
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            anchor = a.get_text(strip=True)
            result["links"].append({"href": href, "text": anchor})

        # Remove irrelevant tags
        for unwanted in soup(['script', 'style', 'noscript', 'header', 'footer', 'nav', 'svg', 'iframe']):
            unwanted.decompose()

        # Extract clean text
        lines = [line.strip() for line in soup.get_text(separator="\n").splitlines()]
        clean_lines = [line for line in lines if line]
        full_text = " ".join(clean_lines)

        result["text"] = full_text

        # Chunk text into sentence/clause candidates for evidence extraction
        raw_sentences = re.split(r'(?<=[.!?\n])\s+', "\n".join(clean_lines))
        result["sentences"] = [s.strip() for s in raw_sentences if len(s.strip()) > 10]
        result["success"] = True

    except requests.exceptions.Timeout:
        result["error"] = "Request timed out while connecting to the server (12s limit)."
    except requests.exceptions.SSLError:
        result["error"] = "SSL Certificate verification error on the target website."
    except requests.exceptions.ConnectionError:
        result["error"] = "Failed to establish network connection to the target URL."
    except Exception as e:
        result["error"] = f"Failed to retrieve webpage: {str(e)}"

    return result
