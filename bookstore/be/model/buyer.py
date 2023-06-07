# import sqlite3 as sqlite
from typing import Tuple, List
from datetime import datetime
import uuid
import json
import logging
# from be.model import db_conn
from be.model.user import User, getBalance
from be.model import error
from be.model.collection import Collection
from be.model.database import user_id_exist, book_id_exist, store_id_exist
import pymongo
import pymongo.errors

class Buyer():
    def __init__(self):
        self.paytimeLimit: int = 900 # 900s
        self.userCollection = Collection("user").collection
        self.userCollection.create_index([("user_id", 1)], unique = True)
        self.storeCollection = Collection("store").collection
        self.storeCollection.create_index([("store_id", 1), ("book_id", 1)], unique = True)
        self.userstoreCollection = Collection("user_store").collection
        self.userstoreCollection.create_index([("user_id", 1), ("store_id", 1)], unique = True)
        self.neworderCollection = Collection("new_order").collection
        self.neworderCollection.create_index([("order_id", 1), ("user_id", 1)], unique = True)
        self.neworderdetailCollection = Collection("new_order_detail").collection
        self.neworderdetailCollection.create_index([("order_id", 1), ("book_id", 1)], unique = True)

    def new_order(self, user_id: str, token: str, store_id: str, id_and_count: List[Tuple[str, int]]) -> Tuple[int, str, str]:
        order_id = ""
        try:
            if not user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id, )
            if not store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id, )
            code, msg = User().check_token (user_id, token)
            if code != 200:
                return code, msg
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
            order_id = uid
            
            total_price = 0
            for book_id, count in id_and_count:
                row = list(self.storeCollection.find({"store_id": store_id, "book_id": book_id}, {"_id": 0, "book_id": 1, "stock_level": 1, "book_info": 1}))
                if len(row) == 0:
                    return error.error_non_exist_book_id(book_id) + (order_id, )

                stock_level = row[0]['stock_level']
                book_info = row[0]['book_info']
                book_info_json = json.loads(book_info)
                price = book_info_json.get("price")
                total_price += count * price

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                result = self.storeCollection.update_many(
                    {"store_id": store_id, "book_id": book_id, "stock_level": {"$gte": count}},
                    {"$inc": {"stock_level": -count}}
                )
                if result.matched_count == 0:
                    return error.error_stock_level_low(book_id) + (order_id, )
                
                result = self.neworderdetailCollection.insert_one({"order_id": order_id, "book_id": book_id, "count": count, "price": price})

            curTime = datetime.now()
            result = self.neworderCollection.insert_one({"order_id": order_id, "store_id": store_id, "user_id": user_id, "order_time": curTime, "total_price": total_price, "paid": 0, "cancelled": 0, "delivered": 0})
        
        except pymongo.errors.PyMongoError as e:
            logging.info("528, {}".format(str(e)))
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            logging.info("530, {}".format(str(e)))
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> Tuple[int, str]:
        try:
            row = list(self.neworderCollection.find({"order_id": order_id}, {"_id": 0, "order_id": 1, "user_id" : 1, "store_id": 1, "order_time": 1, "total_price": 1, "paid": 1, "cancelled": 1}))
            if len(row) == 0:
                return error.error_invalid_order_id(order_id)
            
            order_id = row[0]['order_id']
            buyer_id = row[0]['user_id']
            store_id = row[0]['store_id']
            orderTime = row[0]['order_time']
            total_price = row[0]['total_price']

            if buyer_id != user_id:
                return error.error_authorization_fail()
            
            code, msg = User().check_password (buyer_id, password)
            if code != 200:
                return code, msg
            
            paid = row[0]['paid']
            if paid == 1:
                return error.error_already_paid (order_id)

            cancelled = row[0]['cancelled']
            if cancelled == 1:
                return error.error_order_cancelled (order_id)
            
            curTime = datetime.now()
            timeInterval = curTime - orderTime
            if timeInterval.seconds >= self.paytimeLimit:
                self.neworderCollection.update_one (
                    {"order_id": order_id}, 
                    {"$set": {"cancelled": 1}}
                )
                return error.error_order_cancelled (order_id)

            balance = getBalance (buyer_id)

            row = list(self.userstoreCollection.find({"store_id": store_id}, {"_id": 0, "store_id": 1, "user_id": 1}))
            if len(row) == 0:
                return error.error_non_exist_store_id(store_id)

            seller_id = row[0]['user_id']

            if not user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)

            result = self.userCollection.update_one(
                {"user_id": buyer_id, "balance": {"$gte": total_price}},
                {"$inc": {"balance": -total_price}}
            )
            result = self.userCollection.update_one(
                {"user_id": seller_id},
                {"$inc": {"balance": total_price}}
            )
            result = self.neworderCollection.update_one (
                {"order_id": order_id},
                {"$set": {"paid": 1}}
            )

        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> Tuple[int, str]:
        try:
            code, msg = User().check_password (user_id, password)
            if code != 200:
                return code, msg

            result = self.userCollection.update_one(
                {"user_id": user_id},
                {"$inc": {"balance": add_value}}
            )

        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"
    
    def query_orders (self, user_id, token) -> Tuple [int, str, list]:
        try:
            code, msg = User().check_token (user_id, token)
            if code != 200:
                return code, msg, ""

            orders = []
            order_list = self.neworderCollection.find ({"user_id": user_id}, {"_id": 0, "order_id": 1, "store_id": 1, "order_time": 1, "total_price": 1, "paid": 1, "cancelled": 1})
            for row in order_list:
                cur_order = {}
                cur_order_books = []
                order_id = row['order_id']
                order_time = row['order_time']
                cancelled = row['cancelled']

                curTime = datetime.now()
                timeInterval = curTime - order_time
                if timeInterval.seconds >= self.paytimeLimit:
                    self.neworderCollection.update_one (
                        {"order_id": order_id}, 
                        {"$set": {"cancelled": 1}}
                    )
                    cancelled = 1

                for key in row:
                    cur_order[key] = row[key]
                cur_order['cancelled'] = cancelled
                cursor = self.neworderdetailCollection.find ({"order_id": order_id}, {"_id": 0, "book_id": 1, "count": 1, "price": 1})
                for cur_book_order in cursor:
                    cur_order_books.append (cur_book_order)
                cur_order['order_books'] = cur_order_books
                orders.append (cur_order)
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            return 530, "{}".format(str(e)), ""
        return 200, "ok", orders

    def cancel_order (self, user_id, token, order_id) -> Tuple [int, str]:
        try:
            code, msg = User().check_token (user_id, token)
            if code != 200:
                return code, msg
            order = list (self.neworderCollection.find ({"order_id": order_id}, {"_id": 0, "user_id": 1, "store_id": 1, "order_time": 1, "total_price": 1, "paid": 1, "cancelled": 1}))
            if len (order) == 0:
                return error.error_invalid_order_id(order_id)
            order = order[0]
            order_time = order['order_time']
            curTime = datetime.now()
            timeInterval = curTime - order_time
            if timeInterval.seconds >= self.paytimeLimit:
                self.neworderCollection.update_one (
                    {"order_id": order_id}, 
                    {"$set": {"cancelled": 1}}
                )
                order['cancelled'] = 1
            if order['cancelled'] == 1:
                return error.error_order_cancelled (order_id)
            if order['paid'] == 1:
                buyer_id = order['user_id']
                store_id = order['store_id']
                total_price = order['total_price']
                userStore = list(self.userstoreCollection.find({"store_id": store_id}, {"_id": 0, "user_id": 1}))
                seller_id = userStore[0]['user_id']
                self.userCollection.update_one(
                    {"user_id": buyer_id},
                    {"$inc": {"balance": total_price}}
                )
                self.userCollection.update_one(
                    {"user_id": seller_id},
                    {"$inc": {"balance": -total_price}}
                )
            self.neworderCollection.update_one (
                {"order_id": order_id}, 
                {"$set": {"cancelled": 1}}
            )
        except pymongo.errors.PyMongoError as e:
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
