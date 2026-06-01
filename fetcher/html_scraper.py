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
        if not (url_dict := self._fetch_links()):
            return

        links_dict = self._del_duplicated_links(url_dict)
        self._save_links_in_html(links_dict)
       
    def _fetch_content(self, url_list: list):
        if not url_list:
            return None
        
        response = requests.get(url_list[0], impersonate="chrome", headers=self.headers)
        print(f"[{urlparse(url_list[0]).netloc}] Page: 1, Status: {response.status_code}")

        if response.status_code == 200:
            content_dict = {url_list[0]: response.text}
            if len(url_list) > 1:
                rest = self._fetch_content_with_curl_cffi(url_list[1:])
                if rest:
                    content_dict.update(rest)
        else:
            content_dict = self._fetch_content_with_playwright(url_list)

        if not content_dict:
            return None
        
        return content_dict
    
    def _fetch_content_with_curl_cffi(self, url_list):     
        content_dict = {}

        for i, url in enumerate(url_list, start=2):
            response = requests.get(url, impersonate="chrome", headers=self.headers)
            print(f"[{urlparse(url).netloc}] Page: {i}, Status: {response.status_code}")

            if response.status_code != 200:
                break

            content_dict[url] = response.text

        if not content_dict:
            return None
        return content_dict
    
    def _fetch_content_with_playwright(self, url_list):   
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.chrome_profile,
                executable_path=self.chrome_path,
                headless=False,
                args=["--profile-directory=Default"],
            )

            content_dict = {}

            for i, url in enumerate(url_list, start=1):
                page = context.new_page()
                response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                print(f"[{urlparse(url).netloc}] Page: {i}, Status: {response.status}")

                if i == 1:
                    time.sleep(60)
                else:
                    time.sleep(1)

                if response.status != 200:
                    break

                content_dict[url] = page.content()

            context.close()

        if not content_dict:
            return None
        return content_dict
    
    def _fetch_links(self):
        if not self.max_pages or self.max_pages < 1 or "{page_number}" not in self.url:
            return None

        url_list = [
            self.url.replace(
                "{page_number}",
                str(page_number)
            ) for page_number in range(1, self.max_pages + 1)
        ]

        content_dict = self._fetch_content(url_list)

        if not content_dict:
            return None
        
        url_dict = {}
        for url, content in content_dict.items():
            url_dict[url] = self._make_link_soup(content)
        
        return url_dict
    
    def _make_link_soup(self, content):
        soup = BeautifulSoup(content, "html.parser")

        link_dict = {}
        for link in soup.find_all("a", href=True):
            base_url = f"{urlparse(self.url).scheme}://{urlparse(self.url).netloc}"
            href = link["href"]
            full_href = href if href.startswith("http") else f"{base_url}{href}"
            link_dict[full_href] = {"title": link.get_text(strip=True)}

        return link_dict
    
    def _del_duplicated_links(self, url_dict: dict) -> dict:    
        common = set()
        if len(url_dict) >= 2:
            url_dict_keys = list(url_dict.keys())
            common = set(url_dict[url_dict_keys[0]].keys())
            for url in url_dict_keys[1:]:
                common &= set(url_dict[url].keys())

        link_dict = {}
        for url in url_dict.keys():
            for link in url_dict[url].keys():
                if link not in common:
                    link_dict[link] = url_dict[url][link]

        segments = [urlparse(link).path.split("/")[1] for link in link_dict.keys()]
        counter = Counter(segments)
        total = len(segments)
        dominant = {seg for seg, count in counter.items() if count / total >= 0.2}

        result_dict = {}
        for link in link_dict.keys():
            if urlparse(link).path.split("/")[1] in dominant:
                result_dict[link] = link_dict[link]

        return result_dict
    
    def _save_links_in_html(self, links_dict: dict):
        domain = urlparse(self.url).netloc.replace(".", "_")
        os.makedirs("temp", exist_ok=True)
        filename = f"temp/links_{domain}.html"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("<html><body>\n")
            for link, data in links_dict.items():
                f.write(f"<p><a href='{link}'>{data['title']}</a></p>\n")
            f.write("</body></html>")