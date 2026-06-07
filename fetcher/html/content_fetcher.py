from playwright.sync_api import sync_playwright
from curl_cffi import requests
from urllib.parse import urlparse
from db.queries.content import update_content, get_content_url
import trafilatura
import time

class HTMLContentFetcher():
    def __init__(self, content_id, headers, chrome_profile, path):
        self.content_id = content_id
        self.headers = headers
        self.chrome_profile = chrome_profile
        self.chrome_path = path

    def fetch_content(self):
        time.sleep(5)
        
        update_content(self.content_id, None, "running")

        content_url = get_content_url(self.content_id)
        
        if not content_url:
            return None
        
        content = self._scrap_single_html(content_url)

        if not content:
            update_content(self.content_id, None, "failed")
            return None

        text = trafilatura.extract(
            content,
            include_tables=True,
            include_links=False,
            favor_recall=True,
            include_formatting=True,
            include_images=False
        )

        if not text:
            update_content(self.content_id, None, "failed")
            return None

        if not update_content(self.content_id, text, "completed"):
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
    