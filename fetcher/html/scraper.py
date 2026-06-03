import os
import time
from dotenv import load_dotenv
from fetcher.base_fetcher import BaseFetcher
from playwright.sync_api import sync_playwright
from curl_cffi import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import Counter
from db.queries.link import save_links
from fetcher.html.page_fetcher import HTMLPageFetcher

load_dotenv()

class HTMLScraper(BaseFetcher):
    def __init__(self, fetcher_id, url):
        super().__init__(fetcher_id, url)
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

    def get_page_fetchers(self, link_ids):
        page_fetchers = []

        for link_id in link_ids:
            page_fetchers.append(HTMLPageFetcher(
                link_id,
                self.headers,
                self.chrome_profile,
                self.chrome_path
                )
            )
        
        return page_fetchers

    def fetch_links(self):
        try:
            if not (url_dict := self._scrap_links()):
                print(f"[{self.url}] Błąd: nie pobrano linków")
                return

            if not (links_dict := self._filter_links(url_dict)):
                print(f"[{self.url}] Błąd: nie przefiltrowano linków")
                return

            if not (save_links(self.fetcher_id, links_dict)):
                print(f"[{self.url}] Błąd: nie zapisano linków")
                return
        except Exception as e:
            import traceback
            traceback.print_exc()
            
    def _scrap_links(self):
        if not self.max_pages or self.max_pages < 1 or "{page_number}" not in self.url:
            return None

        url_list = [
            self.url.replace(
                "{page_number}",
                str(page_number)
            ) for page_number in range(1, self.max_pages + 1)
        ]

        if not url_list:
            return None
        
        response = requests.get(url_list[0], impersonate="chrome", headers=self.headers)
        print(f"[{urlparse(url_list[0]).netloc}] Page: 1, Status: {response.status_code}")

        if response.status_code == 200:
            first_links = self._make_link_soup(response.text)
            url_dict = {url_list[0]: first_links}
            if len(url_list) > 1:
                rest = self._scrap_links_with_curl_cffi(url_list[1:], set(first_links.keys()))
                if rest:
                    url_dict.update(rest)
        else:
            url_dict = self._scrap_links_with_playwright(url_list)

        if not url_dict:
            return None
        
        return url_dict
    
    def _scrap_links_with_curl_cffi(self, url_list, first_links):     
        url_dict = {}
        prev_links = None

        for i, url in enumerate(url_list, start=2):
            response = requests.get(url, impersonate="chrome", headers=self.headers)
            print(f"[{urlparse(url).netloc}] Page: {i}, Status: {response.status_code}")

            if response.status_code != 200:
                break

            url_dict[url] = {}
            url_dict[url] = self._make_link_soup(response.text)

            if i >= 3 and prev_links is not None:
                curr_links = set(url_dict[url].keys())
                similarity_prev = len(prev_links & curr_links) / len(prev_links | curr_links)
                similarity_first = len(first_links & curr_links) / len(first_links | curr_links)
                if similarity_prev >= 0.8 or similarity_first >= 0.8:
                    break

            prev_links = set(url_dict[url].keys())

        if not url_dict:
            return None
        return url_dict
    
    def _scrap_links_with_playwright(self, url_list):   
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=self.chrome_profile,
                executable_path=self.chrome_path,
                headless=False,
                args=["--profile-directory=Default"],
            )

            url_dict = {}
            prev_links = None
            first_links = None

            for i, url in enumerate(url_list, start=1):
                page = context.new_page()
                response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                print(f"[{urlparse(url).netloc}] Page: {i}, Status: {response.status}")

                if response.status != 200:
                    break

                url_dict[url] = {}
                url_dict[url] = self._make_link_soup(page.content())

                if i == 1:
                    first_links = set(url_dict[url].keys())

                if i >= 3 and prev_links is not None and first_links is not None:
                    curr_links = set(url_dict[url].keys())
                    similarity_prev = len(prev_links & curr_links) / len(prev_links | curr_links)
                    similarity_first = len(first_links & curr_links) / len(first_links | curr_links)
                    if similarity_prev >= 0.6 or similarity_first >= 0.6:
                        break

                if i == 1:
                    time.sleep(30)
                else:
                    time.sleep(1)

                prev_links = set(url_dict[url].keys())

            context.close()

        if not url_dict:
            return None
        return url_dict

    def _make_link_soup(self, content):
        soup = BeautifulSoup(content, "html.parser")

        link_dict = {}
        for link in soup.find_all("a", href=True):
            base_url = f"{urlparse(self.url).scheme}://{urlparse(self.url).netloc}"
            href = link["href"]
            full_href = href if href.startswith("http") else f"{base_url}{href}"
            parsed = urlparse(full_href)
            clean_href = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            link_dict[clean_href] = link.get_text(strip=True)

        return link_dict
    
    def _filter_links(self, url_dict: dict) -> dict:    
        common = set()
        if len(url_dict) >= 2:
            url_dict_keys = list(url_dict.keys())
            common = set(url_dict[url_dict_keys[0]].keys())
            for url in url_dict_keys[1:3]:
                common &= set(url_dict[url].keys())

        link_dict = {}
        for url in url_dict.keys():
            for link in url_dict[url].keys():
                if link not in common:
                    link_dict[link] = url_dict[url][link]

        # segments = [urlparse(link).path.split("/")[1] for link in link_dict.keys()]
        segments = [parts[1] for link in link_dict.keys() if len(parts := urlparse(link).path.split("/")) > 1]
        counter = Counter(segments)
        total = len(segments)
        dominant = {seg for seg, count in counter.items() if count / total >= 0.2}

        result_dict = {}
        for link in link_dict.keys():
            parts = urlparse(link).path.split("/")
            if len(parts) > 1 and parts[1] in dominant:
                result_dict[link] = link_dict[link]

        return result_dict
        
    # TODO: remove in production
    def _save_links_in_html(self, links_dict: dict):
        domain = urlparse(self.url).netloc.replace(".", "_")
        os.makedirs("temp", exist_ok=True)
        filename = f"temp/links_{domain}.html"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write("<html><body>\n")
            for link, data in links_dict.items():
                f.write(f"<p><a href='{link}'>{data}</a></p>\n")
            f.write("</body></html>")
