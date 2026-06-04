import time
import os
from dotenv import load_dotenv
from fetcher.factory import get_fetchers
from config_manager import set_config
from db.queries.link import get_pending_link_ids, set_links_pending
from concurrent.futures import ThreadPoolExecutor

load_dotenv()

def run_worker():
    while True:
        try:
            config_hash = set_config()
            fetchers = get_fetchers(config_hash)
            set_links_pending()
        except Exception as e:
            print(f"Błąd inicjalizacji: {e}")
            time.sleep(60)
            continue

        with ThreadPoolExecutor(max_workers=len(fetchers)) as executor:
            futures = {executor.submit(fetcher.fetch_links): fetcher for fetcher in fetchers}
            for future, fetcher in futures.items():
                try:
                    future.result()
                except Exception as e:
                    print(f"[{fetcher.url}] Błąd fetch_links: {e}")

        for fetcher in fetchers:
            try:
                pending_link_ids = get_pending_link_ids(fetcher.fetcher_id)
            except Exception as e:
                print(f"Błąd pobierania linków: {e}")
                continue

            try:
                page_fetchers = fetcher.get_page_fetchers(pending_link_ids)
            except Exception as e:
                print(f"Błąd page_fetchers: {e}")
                continue

            if not page_fetchers:
                continue

            with ThreadPoolExecutor(max_workers=int(os.getenv("MAX_WORKERS", 5))) as executor:
                futures = {executor.submit(page_fetcher.fetch_page): page_fetcher for page_fetcher in page_fetchers}
                for future, page_fetcher in futures.items():
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Błąd fetch_page: {e}")

        return  # TODO: remove in production

        time.sleep(int(os.getenv("INTERVAL", 3600)))