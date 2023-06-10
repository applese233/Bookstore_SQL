from be import conf
import re
import base64
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import and_, or_
from be.model.database import getDbSession, Store
from fe.access.book import Book_table


class Search():

    def serializable(book: Book_table):
        return {"id": book.id, "title": book.title, "author": book.author, "publisher": book.publisher, "original_title": book.original_title, "trnaslator": book.translator, "pub_year": book.pub_year, "price": book.price, "binding": book.binding, "tags": book.tags, "picture": base64.b64encode(book.picture).decode('utf-8')}

    def book_info(self, book_id: str, isbn: str):
        try:
            session = getDbSession()
            if not book_id is None:
                book_info = session.query(Book_table).filter(Book_table.id == book_id).first()
            elif not isbn is None:
                book_info = session.query(Book_table).filter(Book_table.isbn == isbn).first()
            else:
                raise BaseException("book_id and isbn both are None")

        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 401, "{}".format(str(e))
        
        def print_dict_types(d, indent=0):
            for key, value in d.items():
                print('  ' * indent + f"{key}: {type(value)}")
                if isinstance(value, dict):
                    print_dict_types(value, indent+1)

        return 200, Search.serializable(book_info)

    def fuzzy_search(self, term: str, store_id: str, page_size: int, page_id: int):
        if page_size is None:
            page_size = conf.default_page_size
        if page_id is None:
            page_id = 0

        # Escape special characters in the search term
        term = re.escape(term)

        # Search term in books' `title`, `author`, `publisher`, `original_title`, `translator`, `tags`, `content` and return all searched books
        try:
            session = getDbSession()
            book_list = []
            if store_id is not None:
                query = session.query(Book_table.id, Book_table.title, Book_table.author, Book_table.publisher, Book_table.original_title, Book_table.translator, Book_table.pub_year, Book_table.price, Book_table.binding, Book_table.tags, Book_table.picture).join(Store).join(Book_table, Store.book_id == Book_table.id).filter(Store.store_id == store_id, or_(Book_table.title.ilike(f'%{term}%'), Book_table.author.ilike(f'%{term}%'), Book_table.publisher.ilike(f'%{term}%'), Book_table.original_title.ilike(f'%{term}%'), Book_table.translator.ilike(f'%{term}%'), Book_table.tags.ilike(f'%{term}%'), Book_table.content.ilike(f'%{term}%')))
                books = query.offset(page_id * page_size).limit(page_size).all()
                total_results = query.count()
            else:
                query = session.query(Book_table).filter(or_(Book_table.title.ilike(f'%{term}%'), Book_table.author.ilike(f'%{term}%'), Book_table.publisher.ilike(f'%{term}%'), Book_table.original_title.ilike(f'%{term}%'), Book_table.translator.ilike(f'%{term}%'), Book_table.tags.ilike(f'%{term}%'), Book_table.content.ilike(f'%{term}%'))).with_entities(Book_table.id, Book_table.title, Book_table.author, Book_table.publisher, Book_table.original_title, Book_table.translator, Book_table.pub_year, Book_table.price, Book_table.binding, Book_table.tags, Book_table.picture)
                books = query.offset(page_id * page_size).limit(page_size).all()
                total_results = query.count()
            for book in books:
                book_list.append(Search.serializable(book))

        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 501, "{}".format(str(e))
        
        return 200, {
            'books': book_list,
            'total_results': total_results,
        }
