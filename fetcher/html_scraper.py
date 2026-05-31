import os
import time
from dotenv import load_dotenv
from fetcher.base_fetcher import BaseFetcher
from playwright.sync_api import sync_playwright
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import Counter

load_dotenv()

class HTMLScraper(BaseFetcher):
    def __init__(self, url):
        super().__init__(url)
        self.chrome_path = os.getenv("CHROME_PATH")
        self.chrome_profile = os.getenv("CHROME_PROFILE")
        self.max_pages = int(os.getenv("MAX_PAGES"))
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.google.com/",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }

    def run_pipeline(self):
        if not (links_dict_list := self._fetch_links()):
            return

        links_dict = self._del_duplicated_links(links_dict_list)

        self._save_links_in_html(links_dict)

    def _del_duplicated_links(self, links: list[dict]) -> dict:
        common = set()
        if len(links) >= 2:
            common = set(links[0].keys())
            for links_dict in links[1:]:
                common &= set(links_dict.keys())

        unique_links_dict = {}
        for links_dict in links:
            for href, title in links_dict.items():
                if href not in common:
                    unique_links_dict[href] = title

        segments = [urlparse(href).path.split("/")[1] for href in unique_links_dict.keys()]
        counter = Counter(segments)
        total = len(segments)
        dominant = {seg for seg, count in counter.items() if count / total >= 0.2}

        result_dict = {
            href: title
            for href, title in unique_links_dict.items()
            if urlparse(href).path.split("/")[1] in dominant
        }
        return result_dict
    
    def _make_links_soup(self, content):
        soup = BeautifulSoup(content, "html.parser")

        links_soup_dict = {}
        for link in soup.find_all("a", href=True):
            base_url = f"{urlparse(self.url).scheme}://{urlparse(self.url).netloc}"
            href = link["href"]
            full_href = href if href.startswith("http") else f"{base_url}{href}"
            links_soup_dict[full_href] = link.get_text(strip=True)

        return links_soup_dict

    def _save_links_in_html(self, links_dict : dict):
        domain = urlparse(self.url).netloc.replace(".", "_")
        os.makedirs("temp", exist_ok=True)
        filename = f"temp/links_{domain}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("<html><body>\n")
            for link, title in links_dict.items():
                f.write(f"<p><a href='{link}'>{title}</a></p>\n")
            f.write("</body></html>")

    def _fetch_content_with_curl_cffi(self, max_pages=1):
        if max_pages < 1:
            return
        
        content_list = []

        if "{page_number}" not in self.url:
            max_pages = 1

        for page_number in range(1, max_pages + 1):
            current_url = self.url.replace("{page_number}", str(page_number))
            response = requests.get(current_url, impersonate="chrome", headers=self.headers)

            print(f"[{urlparse(self.url).netloc}] Page:{page_number} Status: {response.status_code}")

            if response.status_code != 200:
                break

            content_list.append(response.text)

        if not content_list:
            return None
        return content_list

    def _fetch_content_with_playwright(self, max_pages=1):
        if max_pages < 1:
            return
        
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.chrome_profile,
                executable_path=self.chrome_path,
                headless=False,
                args=["--profile-directory=Default"],
            )

            content_list = []

            if "{page_number}" not in self.url:
                max_pages = 1

            for page_number in range(1, max_pages + 1):
                current_url = self.url.replace("{page_number}", str(page_number))
                page = context.new_page()
                response = page.goto(current_url, wait_until="domcontentloaded", timeout=30000)

                print(f"[{urlparse(self.url).netloc}] Page:{page_number} Status: {response.status}")

                time.sleep(30) if page_number == 1 else time.sleep(1)

                if response.status != 200:
                    break

                content_list.append(page.content())

            context.close()

        if not content_list:
            return None
        return content_list

    def _fetch_links(self):
        url = self.url.replace("{page_number}", str(1))
        response = requests.get(url, impersonate="chrome", headers=self.headers)

        if response.status_code == 200:
            content_list = self._fetch_content_with_curl_cffi(self.max_pages)

        else:
            content_list = self._fetch_content_with_playwright(self.max_pages)

        if not content_list:
            return None
        
        return [self._make_links_soup(content) for content in content_list]
    

    