class BaseFetcher:

    def __init__(self, url):
        self.url = url

    def run_pipeline(self):
        raise NotImplementedError
