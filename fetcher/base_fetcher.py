class BaseFetcher:

    def __init__(self, fetcher_id, url):
        self.fetcher_id = fetcher_id
        self.url = url

    def fetch_links(self):
        raise NotImplementedError

    def fetch_page(self, link_id):
        raise NotImplementedError
    
    def get_page_fetchers(self, link_ids):
        raise NotImplementedError
