import os
import trafilatura
import time
from curl_cffi import requests
from db.queries.fetcher import get_or_create_fetcher as db_get_or_create_fetcher
from db.queries.link import save_links as db_save_links
from db.queries.content import get_content_url as db_get_content_url, update_content as db_update_content
from db.queries.embedding import get_embedding_context as db_get_embedding_context, update_embedding as db_update_embedding
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

class Ingester:
    def __init__(self, get_embedding):
        self._fetcher_name = os.getenv("FETCHER_NAME", "curl")
        self.fetcher_id = db_get_or_create_fetcher(self._fetcher_name)
        self.get_embedding = get_embedding

    def fetch_links(self, page_id, url, page_max, page_type):
        if page_type == "paginated" and self._fetcher_name == "curl":
            self._fetch_links_paginated_curl(page_id, url, page_max)
        else:
            raise ValueError(f"Nieznana kombinacja: page_type={page_type}, fetcher={self._fetcher_name}")

    def fetch_content(self, content_id):
        time.sleep(5)
        db_update_content(content_id, None, "running")
        url = db_get_content_url(content_id)
        if not url:
            db_update_content(content_id, None, "failed")
            return
        if self._fetcher_name == "curl":
            text = self._fetch_content_curl(url, content_id)
        else:
            raise ValueError(f"Nieznany fetcher: {self._fetcher_name}")
        if not text:
            db_update_content(content_id, None, "failed")
            return
        db_update_content(content_id, text, "completed")

    def compute_embedding(self, embedding_id):
        db_update_embedding(embedding_id, None, "running")
        result = db_get_embedding_context(embedding_id)
        if not result:
            db_update_embedding(embedding_id, None, "failed")
            print(f"[embedding_id: {embedding_id}] failed")
            return
        content, status, title, url = result
        if status != "completed" or not content:
            db_update_embedding(embedding_id, None, "failed")
            print(f"[embedding_id: {embedding_id}] failed")
            return
        start = len(content) // 10
        end = 9 * len(content) // 10
        text = f"{title}\n{url}\n{content[start:end]}"
        embedding = self.get_embedding(text)
        if not embedding:
            db_update_embedding(embedding_id, None, "failed")
            print(f"[embedding_id: {embedding_id}] failed")
            return
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        db_update_embedding(embedding_id, embedding_str, "completed")
        print(f"[embedding_id: {embedding_id}] completed")

    def _fetch_content_curl(self, url, content_id):
        response = self._fetch_curl(url)
        print(f"[content_id: {content_id}, status: {response.status_code}] {url[:80]}")
        if response.status_code != 200:
            return None
        return trafilatura.extract(
            response.text,
            include_tables=True,
            include_links=False,
            favor_recall=True,
            include_formatting=True,
            include_images=False
        )

    def _fetch_links_paginated_curl(self, page_id, url, page_max):
        if not page_max or "{page_number}" not in url:
            return

        url_dict = {}
        first_links = None
        prev_links = None

        for i in range(1, page_max + 1):
            page_url = url.replace("{page_number}", str(i))
            response = self._fetch_curl(page_url)
            print(f"[page: {i}, status: {response.status_code}] {page_url[:80]}")

            if response.status_code != 200:
                break

            url_dict[page_url] = self._make_link_soup(url, response.text)

            if i == 1:
                first_links = set(url_dict[page_url].keys())

            if i >= 3 and prev_links is not None:
                curr_links = set(url_dict[page_url].keys())
                union_prev = len(prev_links | curr_links)
                union_first = len(first_links | curr_links)
                if ((union_prev > 0 and len(prev_links & curr_links) / union_prev >= 0.8) or
                        (union_first > 0 and len(first_links & curr_links) / union_first >= 0.8)):
                    break

            time.sleep(2)
            prev_links = set(url_dict[page_url].keys())

        if not url_dict:
            return

        links_dict = self._filter_links(url_dict, url)
        if not links_dict:
            return

        db_save_links(page_id, links_dict)

    def _fetch_curl(self, url):
        headers = {
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
        return requests.get(url, impersonate="chrome", headers=headers)

    def _make_link_soup(self, base_url, content):
        soup = BeautifulSoup(content, "html.parser")
        parsed_base = urlparse(base_url)
        base = f"{parsed_base.scheme}://{parsed_base.netloc}"
        link_dict = {}
        for link in soup.find_all("a", href=True):
            href = link["href"]
            full_href = href if href.startswith("http") else f"{base}{href}"
            parsed = urlparse(full_href)
            clean_href = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            link_dict[clean_href] = link.get_text(strip=True)
        return link_dict

    def _filter_links(self, url_dict, base_url):
        common = set()
        if len(url_dict) >= 2:
            keys = list(url_dict.keys())
            common = set(url_dict[keys[0]].keys())
            for url in keys[1:3]:
                common &= set(url_dict[url].keys())

        link_dict = {}
        for url in url_dict:
            for link in url_dict[url]:
                if link not in common:
                    link_dict[link] = url_dict[url][link]

        segments = [parts[1] for link in link_dict if len(parts := urlparse(link).path.split("/")) > 1]
        counter = Counter(segments)
        if not counter:
            return None
        dominant = {max(counter, key=counter.get)}

        return {
            link: link_dict[link]
            for link in link_dict
            if len(parts := urlparse(link).path.split("/")) > 1 and parts[1] in dominant
        }
