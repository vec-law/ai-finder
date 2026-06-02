import os
from dotenv import load_dotenv
from fetcher.base_fetcher import BaseFetcher
from fetcher.html_scraper import HTMLScraper
from fetcher.api_client import APIClient

load_dotenv()

def get_fetchers(config_hash) -> list[BaseFetcher]:
    fetchers = []

    for key, value in os.environ.items():
        if key.startswith("HTML_SEARCH_URL") and value:
            fetchers.append(HTMLScraper(config_hash, url=value))
            
        if key.startswith("API_SEARCH_URL") and value:
            fetchers.append(APIClient(config_hash, url=value))

    return fetchers
