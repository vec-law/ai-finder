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
            set_config()
        except Exception as e:
            print(f"Błąd konfiguracji: {e}")
            return

        threads = []
        for fetcher in get_fetchers():
            thread = Thread(target=fetcher.run_pipeline)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        return

        time.sleep(int(os.getenv("INTERVAL")))