import pytest

from fe.access import search
from fe import conf
from fe.access import book


class TestSearch:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.search = search.Search(conf.URL)
        book_db = book.BookDB()
        self.books = book_db.get_book_info(0, 0)
        yield

    def test_fuzzy_search(self):
        # Check term of title
        for i in range(10):
            self.term = self.books[i].title
            self.store_id = None
            self.page_size = 10
            self.page_id = 0
            code, rst = self.search.fuzzy_search(self.term, self.store_id, self.page_size, self.page_id)
            # Use assert to check the result
            assert code == 200
            assert rst is not None
            assert rst["total_results"] > 0
            assert len(rst["books"]) <= self.page_size
        
        # Check term = "民国" in tags and content
        self.term = "民国"
        self.store_id = None
        self.page_size = 2
        self.page_id = 0
        code, rst = self.search.fuzzy_search(self.term, self.store_id, self.page_size, self.page_id)
        assert code == 200
        assert rst is not None
        assert rst["total_results"] == 3
        assert len(rst["books"]) <= self.page_size

        # Check term = "少年儿童出版社" in publisher
        self.term = "少年儿童出版社"
        self.store_id = None
        self.page_size = 2
        self.page_id = 0
        code, rst = self.search.fuzzy_search(self.term, self.store_id, self.page_size, self.page_id)
        assert code == 200
        assert rst is not None
        assert rst["total_results"] == 6
        assert len(rst["books"]) <= self.page_size

