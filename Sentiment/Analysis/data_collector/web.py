import re

import requests  # requests is useful to 'copy' the website data.
from bs4 import BeautifulSoup  # bs is helping as sorting the data and find the wanted data that we are locking for(also automatically)


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
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned


# ---------- HEADING + PARAGRAPH EXTRACTION ----------
def categorize_headings_with_content(soup: BeautifulSoup):
    categories = {f"h{i}": [] for i in range(1, 5)}
    current = None

    for node in soup.find_all(["h1", "h2", "h3", "h4", "p"]):
        if node.name.startswith("h"):
            text = _clean_text(node.get_text())
            if text:
                current = {"title": text, "paragraphs": []}
                categories[node.name].append(current)

        elif node.name == "p":
            text = _clean_text(node.get_text())
            if text and current is not None:
                current["paragraphs"].append(text)

    return categories


# ---------- MAIN ----------
if __name__ == "__main__":
    session = requests.Session()
    

    website = input("enter a website: ")
    html = get_url(website, session)

    soup = BeautifulSoup(html, "html.parser")
    categorized = categorize_headings_with_content(soup)

    print("\nHeadings and related content:\n")
    for level in sorted(categorized):
        if not categorized[level]:
            continue
        print(level)
        for entry in categorized[level]:
            #print(f"  {entry['title']}")
            for para in entry["paragraphs"]:
                print(f"title : {entry['title']}    - {para}")