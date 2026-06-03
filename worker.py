import time
import os
from dotenv import load_dotenv
from threading import Thread
from fetcher.factory import get_fetchers
from config_manager import set_config
from db.queries.link import get_pending_link_ids
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

def run_worker():
    while True:
        try:
            config_hash = set_config()
        except Exception as e:
            print(f"Błąd konfiguracji: {e}")
            return
        
        try:
            fetchers = get_fetchers(config_hash)
        except Exception as e:
            print(f"Błąd pobierania fetcherów: {e}")
            return

        threads = []
        for fetcher in fetchers:
            thread = Thread(target=fetcher.fetch_links)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        try:
            pending_link_ids = get_pending_link_ids(config_hash)
        except Exception as e:
            print(f"Błąd pobierania id linków: {e}")
            return
        
        for fetcher in fetchers:
            try:
                page_fetchers = fetcher.get_page_fetchers(pending_link_ids)
            except Exception as e:
                print(f"Błąd pobierania fetcherów stron: {e}")
                return
            
            if not page_fetchers:
                continue

            with ThreadPoolExecutor(max_workers=int(os.getenv("MAX_WORKERS", 10))) as executor:
                for page_fetcher in page_fetchers:
                    executor.submit(page_fetcher)

        return # TODO: remove in production

        time.sleep(int(os.getenv("INTERVAL", 3600)))