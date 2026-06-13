import os
from dotenv import load_dotenv
from db.queries.page import get_or_create_page, update_embedding_config as db_update_embedding_config, update_domain as db_update_domain
from db.queries.link import del_expired_links as db_del_expired_links
from db.queries.content import set_content_pending as db_set_content_pending, get_content_ids as db_get_content_ids
from db.queries.embedding import set_embedding_pending as db_set_embedding_pending, get_embedding_ids as db_get_embedding_ids

load_dotenv()

class Page:
    def __init__(self, fetcher_id, embedding_model_name, embedding_vector_size):
        self.url = os.getenv("PAGE_URL")
        self.page_type = os.getenv("PAGE_TYPE")
        self.page_max = int(os.getenv("PAGE_MAX", 1000))
        self.fetcher_id = fetcher_id
        self.embedding_model_name = embedding_model_name
        self.embedding_vector_size = embedding_vector_size
        self.id = get_or_create_page(self.url, self.page_type, self.page_max, self.fetcher_id, self.embedding_model_name, self.embedding_vector_size)
        self.embedding_model_name, self.embedding_vector_size = self._update_embedding_config(embedding_model_name, embedding_vector_size)

    def _update_embedding_config(self, embedding_model_name, embedding_vector_size):
        return db_update_embedding_config(self.id, embedding_model_name, embedding_vector_size)

    def del_expired_links(self):
        db_del_expired_links(self.id)

    def set_content_pending(self):
        db_set_content_pending(self.id)

    def set_embedding_pending(self):
        db_set_embedding_pending(self.id)

    def get_content_ids(self):
        return db_get_content_ids(self.id)

    def get_embedding_ids(self):
        return db_get_embedding_ids(self.id)
    
    def update_domain(self, domain):
        db_update_domain(self.id, domain)
