import pymongo
import pymongo.errors
from be.model.collection import Collection
from be import conf
import re
import base64


class Search():

    def __init__(self):
        self.bookCollection = Collection("book").collection
        self.bookCollection.create_index([("id", 1)], unique=True)
        self.bookCollection.create_index([("title", 1), ("author", 1), (
            "publisher", 1), ("original_title", 1), ("translator", 1), ("tags", 1)])
        self.bookCollection.create_index([("content", "text")])
        
        self.storeCollection = Collection("store").collection
        self.storeCollection.create_index([("store_id", 1), ("book_id", 1)], unique=True)

    def serializable(book: dict):
        book.pop("_id")
        book["picture"] = base64.b64encode(book["picture"]).decode('utf-8')
        return book

    def book_info(self, book_id: str, isbn: str):
        try:
            if not book_id is None:
                book_info = self.bookCollection.find_one({"id": book_id})
            elif not isbn is None:
                book_info = self.bookCollection.find_one({"isbn": isbn})
            else:
                raise BaseException("book_id and isbn both are None")

        except pymongo.errors.PyMongoError as e:
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
            book_list = []
            query = {
                "$or": [
                    {"title": {"$regex": term, "$options": "i"}},
                    {"author": {"$regex": term, "$options": "i"}},
                    {"publisher": {"$regex": term, "$options": "i"}},
                    {"original_title": {"$regex": term, "$options": "i"}},
                    {"translator": {"$regex": term, "$options": "i"}},
                    {"tags": {"$regex": term, "$options": "i"}},
                    {"content": {"$regex": term, "$options": "i"}}
                ]
            }
            if store_id is not None:
                pipeline = [
                    {"$match": {
                        "store_id": store_id
                    }},
                    {"$lookup": {
                        "from": "book",
                        "localField": "book_id",
                        "foreignField": "id",
                        "as": "book"
                    }},
                    {"$unwind": "$book"},
                    {"$match": query},
                    {
                        "$project": {
                            "id": "$book.id",
                            "title": "$book.title",
                            "author": "$book.author",
                            "publisher": "$book.publisher",
                            "original_title": "$book.original_title",
                            "translator": "$book.translator",
                            "pub_year": "$book.pub_year",
                            "price": "$book.price",
                            "binding": "$book.binding",
                            "tags": "$book.tags",
                            "picture": "$book.picture"
                        }
                    },
                    {"$skip": page_id * page_size},
                    {"$limit": page_size}
                ]
                books = self.storeCollection.aggregate(pipeline)
                total_results = len(list(self.storeCollection.aggregate(pipeline[:-2])))
            else:
                books = self.bookCollection.find(query, {"id": 1, "title": 1, "author": 1, "publisher": 1, "original_title": 1, "translator": 1,
                                             "pub_year": 1, "price": 1, "binding": 1, "tags": 1, "picture": 1}).skip(page_id * page_size).limit(page_size)
                total_results = self.bookCollection.count_documents(query)
            for book in books:
                book_list.append(Search.serializable(book))

        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 501, "{}".format(str(e))
        
        return 200, {
            'books': book_list,
            'total_results': total_results,
        }
