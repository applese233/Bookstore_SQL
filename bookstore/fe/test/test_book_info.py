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

    def test_book_info(self):
        # Randomly select a book from self.books and search it
        for i in range(10):
            if i % 2 == 0:
                self.book_id = self.books[i].id
                self.isbn = None
            else:
                self.book_id = None
                self.isbn = self.books[i].isbn
            code, info = self.search.book_info(self.book_id, self.isbn)
            # Use assert to check the result
            assert code == 200
            assert info is not None
            # Check whether all fileds of info of the book are correct
            assert info["title"] == self.books[i].title
            assert info["author"] == self.books[i].author
            assert info["publisher"] == self.books[i].publisher
            # Check whether all element of tags list are correct
            assert info["tags"] == '\n'.join(self.books[i].tags) + '\n'

