from typing import Tuple
import requests
from urllib.parse import urljoin
import json as js

class Search:
    def __init__(self, url_prefix):
        self.url_prefix = urljoin(url_prefix, "search/")

    def book_info(self, book_id: str, isbn: str) -> Tuple[int, dict]:
        json = {"book_id": book_id, "isbn": isbn}
        url = urljoin(self.url_prefix, "book_info")
        r = requests.post(url, json=json)
        return r.status_code, r.json().get("book_info")
    
    def fuzzy_search(self, term: str, store_id: str, page_size: int, page_id: int) -> Tuple[int, dict]:
        json = {"term": term, "store_id": store_id, "page_size": page_size, "page_id": page_id}
        url = urljoin(self.url_prefix, "fuzzy_search")
        r = requests.post(url, json=json)
        return r.status_code, r.json().get("rst")