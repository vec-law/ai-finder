from playwright.sync_api import sync_playwright
from curl_cffi import requests
from urllib.parse import urlparse
from db.queries.link import get_link_url, update_link
import trafilatura
from embeddings import get_embedding

class HTMLPageFetcher():
    def __init__(self, link_id, headers, chrome_profile, path):
        self.link_id = link_id
        self.headers = headers
        self.chrome_profile = chrome_profile
        self.chrome_path = path

    def fetch_page(self):
        update_link(self.link_id, None, None, "running")

        link_url = get_link_url(self.link_id)
        
        if not link_url:
            return None
        
        content = self._scrap_single_html(link_url)

        if not content:
            update_link(self.link_id, None, None, "failed")
            return None

        text = trafilatura.extract(
            content,
            include_tables=True,
            include_links=False,
            favor_recall=True
        )

        if not text:
            update_link(self.link_id, None, None, "failed")
            return None

        embedding = get_embedding("passage: " + text)

        if not update_link(self.link_id, text, embedding, "completed"):
            return None

        return text

    def _scrap_single_html(self, url):
        if not url:
            return None

        response = requests.get(url, impersonate="chrome", headers=self.headers)
        print(f"[{urlparse(url).netloc}] Status: {response.status_code}")

        if response.status_code == 200:
            return response.text

        return self._scrap_single_html_with_playwright(url)

    def _scrap_single_html_with_playwright(self, url):
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.chrome_profile,
                executable_path=self.chrome_path,
                headless=False,
                args=["--profile-directory=Default"],
            )

            page = context.new_page()
            response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
            html = page.content() if response.status == 200 else None
            context.close()

            return html
    