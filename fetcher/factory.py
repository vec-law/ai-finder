import os
from dotenv import load_dotenv
from fetcher.base_fetcher import BaseFetcher
from fetcher.html.fetcher import HTMLFetcher
from fetcher.api_client import APIClient
from db.queries.fetcher import save_fetcher

load_dotenv()

def get_fetchers(config_id) -> list[BaseFetcher]:
    fetchers = []

    for key, value in os.environ.items():
        if key.startswith("HTML_SEARCH_URL") and value:
            fetcher_id = save_fetcher(config_id, value)
            fetchers.append(HTMLFetcher(fetcher_id, url=value))
            
        if key.startswith("API_SEARCH_URL") and value:
            fetcher_id = save_fetcher(config_id, value)
            fetchers.append(APIClient(fetcher_id, url=value))

    return fetchers
