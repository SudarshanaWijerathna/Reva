import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_adaderana_headlines(max_articles=10):
    """
    Fetch latest headlines from Ada Derana English.
    Returns list of dicts: {title, url, timestamp}
    """
    url = "https://www.adaderana.lk"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        headlines = []
        # Ada Derana uses h3 > a for main headlines
        for item in soup.select('h4 a')[:max_articles]:
            title = item.get_text(strip=True)
            link = item.get('href')
            if title and link:
                # Ensure full URL
                if link.startswith('/'):
                    link = 'https://www.adaderana.lk' + link
                headlines.append({
                    "title": title,
                    "url": link,
                    "timestamp": datetime.now().isoformat(),
                    "source": "Ada Derana"
                })
        return headlines
    except Exception as e:
        logger.error(f"Ada Derana scrape failed: {e}")
        return []
    

def fetch_dailyft_headlines(max_articles=10):
    """
    Fetch latest headlines from DailyFT (English business news, Sri Lanka).
    """
    url = "https://www.dailyft.lk"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        headlines = []
        # DailyFT uses h4 > a inside .news-item
        for item in soup.select('.news-item h4 a')[:max_articles]:
            title = item.get_text(strip=True)
            link = item.get('href')
            if title and link:
                if link.startswith('/'):
                    link = 'https://www.dailyft.lk' + link
                headlines.append({
                    "title": title,
                    "url": link,
                    "timestamp": datetime.now().isoformat(),
                    "source": "DailyFT"
                })
        return headlines
    except Exception as e:
        logger.error(f"DailyFT scrape failed: {e}")
        return []
    

def fetch_hirunews_english_headlines(max_articles=10):
    """
    Scrape English headlines from Hiru News: https://www.hirunews.lk/en/
    """
    url = "https://www.hirunews.lk/en/"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        headlines = []
        # From your HTML: .card-v1 → .card-title-v1
        for card in soup.select('a.card-v1')[:max_articles]:
            title_elem = card.select_one('.card-title-v1')
            if not title_elem:
                continue
            title = title_elem.get_text(strip=True)
            link = card.get('href')
            if title and link:
                # Ensure absolute URL
                if link.startswith('/'):
                    link = 'https://www.hirunews.lk' + link
                headlines.append({
                    "title": title,
                    "url": link,
                    "timestamp": datetime.now().isoformat(),
                    "source": "Hiru News (English)"
                })
        return headlines
    except Exception as e:
        logger.error(f"Hiru News (English) scrape failed: {e}")
        return []
    
def fetch_newswire_headlines(max_articles=10):
    """
    Scrape headlines from NewsWire.lk (https://www.newswire.lk)
    Uses .posts-listunit-title > a selector (confirmed from live HTML)
    """
    url = "https://www.newswire.lk"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        headlines = []
        # Target the exact class from your HTML
        for item in soup.select('.posts-listunit-title a.posts-listunit-link')[:max_articles]:
            title = item.get_text(strip=True)
            link = item.get('href')
            if title and link:
                # Ensure absolute URL
                if link.startswith('/'):
                    link = 'https://www.newswire.lk' + link
                headlines.append({
                    "title": title,
                    "url": link,
                    "timestamp": datetime.now().isoformat(),
                    "source": "NewsWire"
                })
        return headlines
    except Exception as e:
        logger.error(f"NewsWire scrape failed: {e}")
        return []
print("hello world")
print("adaderana headlines:", fetch_adaderana_headlines(5))
print("dailyft headlines:", fetch_dailyft_headlines(5))
print("hirunews english headlines:", fetch_hirunews_english_headlines(5))
print("newswire headlines:", fetch_newswire_headlines(5))

