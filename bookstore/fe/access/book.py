import os
from typing import List
import random
import base64
import simplejson as json
from sqlalchemy import Column, String, Integer, Text, LargeBinary, create_engine
from be.model.database import getDatabaseBase, getDbSession

Base = getDatabaseBase()

class Book_table(Base):
    __tablename__ = "book"

    id = Column(Text, primary_key = True, nullable = False)
    title = Column(Text)
    author = Column(Text)
    publisher = Column(Text)
    original_title = Column(Text)
    translator = Column(Text)
    pub_year = Column(Text)
    pages = Column(Integer)
    price = Column(Integer)
    currency_unit = Column(Text)
    binding = Column(Text)
    isbn = Column(Text)
    author_intro = Column(Text)
    book_intro = Column(Text)
    content = Column(Text)
    tags = Column(Text)
    picture = Column(LargeBinary)

class Book:
    id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    pub_year: str
    pages: int
    price: int
    currency_unit: str
    binding: str
    isbn: str
    author_intro: str
    book_intro: str
    content: str
    tags: List[str]
    picture: List[bytes]

    def __init__(self):
        self.tags = []
        self.picture = []


class BookDB:
    def __init__(self, large: bool = False):
        pass

    def get_book_count(self):
        return len(getDbSession().query(Book_table).all())

    def get_book_info(self, start, size) -> List[Book]:
        books = []
        result = getDbSession().query(Book_table).order_by(Book_table.id).offset(start).limit(size).all()
        for row in result:
            book = Book()
            book.id = row.id
            book.title = row.title
            book.author = row.author
            book.publisher = row.publisher
            book.original_title = row.original_title
            book.translator = row.translator
            book.pub_year = row.pub_year
            book.pages = row.pages
            book.price = row.price
            book.currency_unit = row.currency_unit
            book.binding = row.binding
            book.isbn = row.isbn
            book.author_intro = row.author_intro
            book.book_intro = row.book_intro
            book.content = row.content
            tags = row.tags
            picture = row.picture
            for tag in tags.split("\n"):
                if tag.strip() != "":
                    book.tags.append(tag)
            for i in range(0, random.randint(0, 9)):
                if picture is not None:
                    encode_str = base64.b64encode(picture).decode('utf-8')
                    book.picture.append(encode_str)
            books.append(book)

        return books


