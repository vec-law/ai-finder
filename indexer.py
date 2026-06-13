import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from embedder import Embedder
from ingester import Ingester
from page import Page
from rag import RAG

def run_indexer():
    while True:
        try:
            embedder = Embedder()

            ingester = Ingester(embedder.get_embedding)

            page = Page(
                ingester.fetcher_id,
                embedder.model_name,
                embedder.vector_size
            )

            rag = RAG(embedder)

            page.update_domain(rag.get_domain(page.url))

            page.del_expired_links()
            ingester.fetch_links(
                page.id,
                page.url,
                page.page_max,
                page.page_type
            )

            page.set_content_pending()
            content_ids = page.get_content_ids()

            with ThreadPoolExecutor(max_workers=2) as executor:
                executor.map(ingester.fetch_content, content_ids)

            page.set_embedding_pending()
            embedding_ids = page.get_embedding_ids()

            with ThreadPoolExecutor(max_workers=2) as executor:
                executor.map(ingester.compute_embedding, embedding_ids)

            page.del_incomplete_links()

        except Exception as e:
            traceback.print_exc()
            print(f"Błąd: {e}")
            time.sleep(60)
            continue
        time.sleep(3600)
