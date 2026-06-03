class BaseFetcher:

    def __init__(self, config_hash, url):
        self.config_hash = config_hash
        self.url = url

    def fetch_links(self):
        raise NotImplementedError

    def fetch_page(self, link_id):
        raise NotImplementedError
    
    def get_page_fetchers(self, link_ids):
        raise NotImplementedError
