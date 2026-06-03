import time
import os
from dotenv import load_dotenv
from threading import Thread
from fetcher.factory import get_fetchers
from config_manager import set_config

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
            thread = Thread(target=fetcher.scrap_links)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        return # TODO: remove in production

        time.sleep(int(os.getenv("INTERVAL", 3600)))