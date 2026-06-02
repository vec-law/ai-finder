class BaseFetcher:

    def __init__(self, config_hash, url):
        self.config_hash = config_hash
        self.url = url

    def run_pipeline(self):
        raise NotImplementedError
