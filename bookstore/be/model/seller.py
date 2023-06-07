# import sqlite3 as sqlite
from typing import Tuple
import pymongo
import pymongo.errors
from be.model import error
# from be.model import db_conn
from be.model.collection import Collection
from be.model.database import user_id_exist, book_id_exist, store_id_exist

class Seller():

    def __init__(self):
        # db_conn.DBConn.__init__(self)
        self.storeCollection = Collection("store").collection
        self.storeCollection.create_index([("store_id", 1), ("book_id", 1)], unique=True)
        self.userStoreCollection = Collection ("user_store").collection
        self.userStoreCollection.create_index ([("user_id", 1), ("store_id", 1)], unique=True)
        self.neworderCollection = Collection("new_order").collection
        self.neworderCollection.create_index([("order_id", 1), ("user_id", 1)], unique = True)
        self.neworderdetailCollection = Collection("new_order_detail").collection
        self.neworderdetailCollection.create_index([("order_id", 1), ("book_id", 1)], unique = True)

    def add_book(self, user_id: str, store_id: str, book_id: str, book_json_str: str, stock_level: int):
        try:
            if not user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            # self.conn.execute("INSERT into store(store_id, book_id, book_info, stock_level)"
            #                   "VALUES (?, ?, ?, ?)", (store_id, book_id, book_json_str, stock_level))
            # self.conn.commit()

            self.storeCollection.insert_one (
                {
                    "store_id": store_id, 
                    "book_id": book_id, 
                    "book_info": book_json_str, 
                    "stock_level": stock_level
                }
            )
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def add_stock_level(self, user_id: str, store_id: str, book_id: str, add_stock_level: int):
        try:
            if not user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            # self.conn.execute("UPDATE store SET stock_level = stock_level + ? "
            #                   "WHERE store_id = ? AND book_id = ?", (add_stock_level, store_id, book_id))
            # self.conn.commit()
            update_result = self.storeCollection.update_one (
                {"store_id": store_id, "book_id": book_id},
                {"$inc": {"stock_level": add_stock_level}}
            )
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def create_store(self, user_id: str, store_id: str) -> Tuple[int, str]:
        try:
            if not user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if store_id_exist(store_id):
                return error.error_exist_store_id(store_id)
            # self.conn.execute("INSERT into user_store(store_id, user_id)"
            #                   "VALUES (?, ?)", (store_id, user_id))
            # self.conn.commit()
            self.userStoreCollection.insert_one (
                {
                    "store_id": store_id, 
                    "user_id": user_id
                }
            )
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def deliver_order(self, order_id: str) -> Tuple[int, str]:
        try:
            order = list (self.neworderCollection.find ({"order_id": order_id}, {"_id": 0, "user_id": 1, "store_id": 1, "order_time": 1, "total_price": 1, "paid": 1, "cancelled": 1, "delivered": 1}))
            if len(order) == 0:
                return error.error_invalid_order_id(order_id)
            if order[0]['paid'] == 0:
                return error.error_order_not_paid(order_id)
            if order[0]['cancelled'] == 1:
                return error.error_order_already_cancelled(order_id)
            if order[0]['delivered'] == 1:
                return error.error_order_already_delivered(order_id)
            store_id = order[0]['store_id']
            if not store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            detailed_order = list(self.neworderdetailCollection.find({"order_id": order_id}, {"_id": 0, "book_id": 1, "count": 1}))
            if len(detailed_order) == 0:
                return error.error_invalid_order_id(order_id)
            for each in detailed_order:
                book_id = each['book_id']
                count = each['count']
                if not book_id_exist(store_id, book_id):
                    return error.error_non_exist_book_id(book_id)
                result = self.storeCollection.update_one({"store_id": store_id, "book_id": book_id}, {"$inc": {"stock_level": -count}})
                if result.matched_count == 0:
                    return error.error_stock_level_low(book_id)
            result = self.neworderCollection.update_one({"order_id": order_id}, {"$set": {"delivered": 1}})
            if result.matched_count == 0:
                return error.error_invalid_order_id(order_id)
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
