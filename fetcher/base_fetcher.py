class BaseFetcher:

    def __init__(self, fetcher_id, url):
        self.fetcher_id = fetcher_id
        self.url = url

    def fetch_links(self):
        raise NotImplementedError
    
    def get_content_fetchers(self, content_ids):
        raise NotImplementedError
