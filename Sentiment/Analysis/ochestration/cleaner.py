#from Sentiment.Analysis.data_collector.news_api import everything
import re


class TextCleaner:
    def __init__(self, size: int = 500):
        # Precompiled regex patterns for performance
        self.url_pattern = re.compile(r'https?://\S+|www\.\S+')
        self.html_pattern = re.compile(r'<.*?>')
        self.non_alpha_pattern = re.compile(r'[^a-zA-Z\s]')
        self.multiple_spaces_pattern = re.compile(r'\s+')
        self.size = size

    def clean_text(self, article_json:dict)->str:    
        """
        takes news api json text and clean it
        """
        title = article_json.get('title', '')
        desc = article_json.get('description', '')
        content = article_json.get('content', '')

        text = f"{title} {desc} {content}"
        
        text = text.lower()
        text = self.url_pattern.sub('', text)
        text = self.html_pattern.sub('', text)
        text = self.non_alpha_pattern.sub(' ', text)
        text = self.multiple_spaces_pattern.sub(' ', text).strip()

        return text[:self.size].strip()
    
    def clean_text_from_scraper(self, text:str)->str:
        """
        takes text from news scraper and clean it
        """
        text = text.lower()
        text = self.url_pattern.sub('', text)
        text = self.html_pattern.sub('', text)
        text = self.non_alpha_pattern.sub(' ', text)
        cleaned = self.multiple_spaces_pattern.sub(' ', text).strip()

        return cleaned[:self.size]
    
'''clean = TextCleaner()
list_of_cleaned_texts = []
for article in everything:
    cleaned_text = clean.clean_text(article)
    list_of_cleaned_texts.append(cleaned_text)
    print(f"Cleaned Text: {cleaned_text}\n")'''