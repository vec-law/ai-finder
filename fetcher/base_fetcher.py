class BaseFetcher:

    def __init__(self, config_hash, url):
        self.config_hash = config_hash
        self.url = url

    def fetch_links(self):
        raise NotImplementedError

    def fetch_page(self):
        raise NotImplementedError
    
    def get_page_fetchers(self):
        raise NotImplementedError
