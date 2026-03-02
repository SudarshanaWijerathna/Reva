
import re
import requests  # requests is useful to 'copy' the website data.
from bs4 import BeautifulSoup  # bs is helping as sorting the data and find the wanted data that we are locking for(also automatically)

# ============= Possible Sites to test =============
# https://www.dailymirror.lk/
# https://www.dailymirror.lk/latest-news/108


# ---------- URL NORMALIZER ----------
def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith(("http://", "https://")):
        return raw
    return f"https://{raw}"


# ---------- FETCH PAGE ----------
def get_url(url: str, session: requests.Session) -> str:
    normalized = normalize_url(url)
    response = session.get(normalized, timeout=30)

    if response.status_code == 200:
        return response.text

    raise ValueError(
        f"Unable to fetch {normalized}: status {response.status_code}. "
        "Site may be blocking automated access."
    )


# ---------- TEXT CLEANER ----------
def _clean_text(value: str) -> str:
    # Remove time stamps like "3 hours ago", "4 days ago", etc.
    cleaned = re.sub(r"\d+\s+(?:hours?|days?|minutes?|seconds?|weeks?|months?|years?)\s+ago\s*[-–]?\s*", "", value)
    # Remove dates like "20 Feb 2026", "15 January 2025", etc.
    cleaned = re.sub(r"\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\s*[-–]?\s*", "", cleaned)
    # Remove extra whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


# ---------- HEADING + PARAGRAPH EXTRACTION ----------
def categorize_headings_with_content(soup: BeautifulSoup):
    headings =[]
    content = []

    for node in soup.find_all(["h1", "h2", "h3", "h4", "p"]):
        if node.name.startswith("h"):
            text = _clean_text(node.get_text())
            if text:
                headings.append(text)

        elif node.name == "p":
            text = _clean_text(node.get_text())
            if text:
                content.append(text)

    return headings, content

# -----------Paragraph extractor -----------
def extract_paragraphs(soup: BeautifulSoup):
    paragraphs = []
    for p in soup.find_all("p"):
        text = _clean_text(p.get_text())
        if text:
            paragraphs.append(text)
    return paragraphs

# ---------- MAIN ----------
#if __name__ == "__main__":
def web_scraper():

    sites = [
        "https://www.dailymirror.lk/",
        "https://www.dailymirror.lk/latest-news/108",
    ]
    for site in sites:
        print(f"Scraping {site}...=======================================")

        try:
            session = requests.Session()
            website = site
            html = get_url(website, session)

            soup = BeautifulSoup(html, "html.parser")
            headings, content = categorize_headings_with_content(soup)
            paragraphs = extract_paragraphs(soup)

            print("headings============, lengths", len(headings))
            print("content============, lengths", len(content))
            print("paragraphs============, lengths", len(paragraphs))
            
            return {
                "headings": headings,
                "content": content,
                "paragraphs": paragraphs
            }
        
        except ValueError as e:
            print(f"Error fetching {site}: {e}")
        except requests.RequestException as e:
            print(f"Request error for {site}: {e}")
        except Exception as e:
            print(f"Unexpected error processing {site}: {e}")
