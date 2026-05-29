import time
import os
from dotenv import load_dotenv
from threading import Thread
from fetcher.factory import get_fetchers

load_dotenv()

def run_worker():
    while True:
        for fetcher in get_fetchers():
            thread = Thread(target=fetcher.fetch_items)
            thread.start()
        time.sleep(int(os.getenv("INTERVAL")))
