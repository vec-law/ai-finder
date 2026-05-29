class BaseFetcher:

    def fetch_items(self):
        raise NotImplementedError

    def save_item(self, title: str, content: str) -> None:
        pass
