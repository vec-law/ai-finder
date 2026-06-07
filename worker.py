import time
import os
from dotenv import load_dotenv
from fetcher.factory import get_fetchers
from config_manager import set_config
from db.queries.link import del_expired_links
from db.queries.content import set_contents_pending, get_pending_content_ids
from db.queries.embedding import set_embeddings_pending, get_pending_embedding_ids
from concurrent.futures import ThreadPoolExecutor
from content_embedder import ContentEmbedder

load_dotenv()

def run_worker():
    while True:
        try:
            config_id = set_config()
            fetchers = get_fetchers(config_id)
            del_expired_links(config_id)
            set_contents_pending()
            set_embeddings_pending()
        except Exception as e:
            print(f"Błąd inicjalizacji: {e}")
            time.sleep(60)
            continue

        # with ThreadPoolExecutor(max_workers=1) as executor:
        #     futures = {executor.submit(fetcher.fetch_links): fetcher for fetcher in fetchers}
        #     for future, fetcher in futures.items():
        #         try:
        #             future.result()
        #         except Exception as e:
        #             print(f"[{fetcher.url}] Błąd fetch_links: {e}")

        # for fetcher in fetchers:
        #     try:
        #         pending_content_ids = get_pending_content_ids(fetcher.fetcher_id)
        #     except Exception as e:
        #         print(f"Błąd pobierania contentów: {e}")
        #         continue

        #     try:
        #         content_fetchers = fetcher.get_content_fetchers(pending_content_ids)
        #     except Exception as e:
        #         print(f"Błąd content_fetchers: {e}")
        #         continue

        #     if not content_fetchers:
        #         continue

        #     with ThreadPoolExecutor(max_workers=2) as executor:
        #         futures = {executor.submit(content_fetcher.fetch_content): content_fetcher for content_fetcher in content_fetchers}
        #         for future, content_fetcher in futures.items():
        #             try:
        #                 future.result()
        #             except Exception as e:
        #                 print(f"Błąd fetch_content: {e}")

        for fetcher in fetchers:
            try:
                pending_embedding_ids = get_pending_embedding_ids(fetcher.fetcher_id)
            except Exception as e:
                print(f"Błąd pobierania embeddingów: {e}")
                continue

            embedders = [ContentEmbedder(embedding_id) for embedding_id in pending_embedding_ids]

            if not embedders:
                continue

            with ThreadPoolExecutor(max_workers=int(os.getenv("MAX_WORKERS", 5))) as executor:
                futures = {executor.submit(embedder.embed): embedder for embedder in embedders}
                for future, embedder in futures.items():
                    try:
                        future.result()
                    except Exception as e:
                        print(f"Błąd embed: {e}")

        return  # TODO: remove in production

        time.sleep(int(os.getenv("INTERVAL", 3600)))