from typing import Tuple, List
from datetime import datetime
import uuid
import json
import logging
from sqlalchemy.exc import SQLAlchemyError
from be.model.user import User, getBalance
from be.model import error
from be.model.database import user_id_exist, book_id_exist, store_id_exist, getDbSession, User_store, Store, New_order, New_order_detail


class Buyer():
    def __init__(self):
        self.paytimeLimit: int = 900 # 900s

    def new_order(self, user_id: str, token: str, store_id: str, id_and_count: List[Tuple[str, int]]) -> Tuple[int, str, str]:
        order_id = ""
        try:
            if not user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id, )
            if not store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id, )
            code, msg = User().check_token(user_id, token)
            if code != 200:
                return code, msg
            uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))
            order_id = uid
            
            total_price = 0
            session = getDbSession()
            for book_id, count in id_and_count:
                row = session.query(Store).filter(Store.store_id == store_id, Store.book_id == book_id).all()
                if len(row) == 0:
                    return error.error_non_exist_book_id(book_id) + (order_id, )

                stock_level = row[0].stock_level
                book_info = row[0].book_info
                book_info_json = json.loads(book_info)
                price = book_info_json.get("price")
                total_price += count * price

                if stock_level < count:
                    return error.error_stock_level_low(book_id) + (order_id,)

                result = session.query(Store).filter(Store.store_id == store_id, Store.book_id == book_id, Store.stock_level >= count).all()
                if len(result) == 0:
                    return error.error_stock_level_low(book_id) + (order_id, )
                
                session.add(New_order_detail(order_id = order_id, book_id = book_id, count = count, price = price))
                session.commit()

            cur_time = datetime.now()
            session.add(New_order(order_id = order_id, store_id = store_id, user_id = user_id, order_time = cur_time, total_price = total_price, paid = 0, cancelled = 0, delivered = 0))
            session.commit()
        
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> Tuple[int, str]:
        try:
            session = getDbSession()
            row = session.query(New_order).filter(New_order.order_id == order_id).all()
            if len(row) == 0:
                return error.error_invalid_order_id(order_id)
            
            order_id = row[0].order_id
            buyer_id = row[0].user_id
            store_id = row[0].store_id
            orderTime = row[0].order_time
            total_price = row[0].total_price

            if buyer_id != user_id:
                return error.error_authorization_fail()
            
            code, msg = User().check_password (buyer_id, password)
            if code != 200:
                return code, msg
            
            paid = row[0].paid
            if paid == 1:
                return error.error_already_paid (order_id)

            cancelled = row[0].cancelled
            if cancelled == 1:
                return error.error_order_cancelled (order_id)
            
            curTime = datetime.now()
            timeInterval = curTime - orderTime
            if timeInterval.seconds >= self.paytimeLimit:
                session.query(New_order).filter(New_order.order_id == order_id).update({New_order.cancelled: 1})
                session.commit()
                return error.error_order_cancelled (order_id)

            balance = getBalance (buyer_id)

            row = session.query(User_store).filter(User_store.store_id == store_id).all()
            if len(row) == 0:
                return error.error_non_exist_store_id(store_id)

            seller_id = row[0].user_id

            if not user_id_exist(seller_id):
                return error.error_non_exist_user_id(seller_id)

            if balance < total_price:
                return error.error_not_sufficient_funds(order_id)

            session.query(User).filter(User.user_id == buyer_id, User.balance >= total_price).update({User.balance: User.balance - total_price})
            session.query(User).filter(User.user_id == seller_id).update({User.balance: User.balance + total_price})
            session.query(New_order).filter(New_order.order_id == order_id).update({New_order.paid: 1})
            session.commit()

        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))

        except BaseException as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> Tuple[int, str]:
        try:
            code, msg = User().check_password (user_id, password)
            if code != 200:
                return code, msg

            session = getDbSession()
            session.query(User).filter(User.user_id == user_id).update({User.balance: User.balance + add_value})
            session.commit()

        except SQLAlchemyError as e:
            session.rollback()
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
            session = getDbSession()
            order_list = session.query(New_order).filter(New_order.user_id == user_id).all()
            for row in order_list:
                cur_order = {}
                cur_order_books = []
                order_id = row.order_id
                order_time = row.order_time
                cancelled = row.cancelled

                curTime = datetime.now()
                timeInterval = curTime - order_time
                if timeInterval.seconds >= self.paytimeLimit:
                    session.query(New_order).filter(New_order.order_id == order_id).update({New_order.cancelled: 1})
                    session.commit()
                    cancelled = 1

                cur_order['order_id'] = row.order_id
                cur_order['store_id'] = row.store_id
                cur_order['order_time'] = row.order_time
                cur_order['total_price'] = row.total_price
                cur_order['paid'] = row.paid
                cur_order['cancelled'] = cancelled
                cursor = session.query(New_order_detail).filter(New_order_detail.order_id == order_id).all()
                for cur_book_order in cursor:
                    cur_order_books.append (cur_book_order.Formulate())
                cur_order['order_books'] = cur_order_books
                orders.append (cur_order)
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            print(str(e))
            return 530, "{}".format(str(e)), ""
        return 200, "ok", orders

    def cancel_order (self, user_id, token, order_id) -> Tuple [int, str]:
        try:
            code, msg = User().check_token (user_id, token)
            if code != 200:
                return code, msg
            session = getDbSession()
            order = session.query(New_order).filter(New_order.order_id == order_id).all()
            if len (order) == 0:
                return error.error_invalid_order_id(order_id)
            order = order[0]
            order_time = order.order_time
            curTime = datetime.now()
            timeInterval = curTime - order_time
            if timeInterval.seconds >= self.paytimeLimit:
                session.query(New_order).filter(New_order.order_id == order_id).update({New_order.cancelled: 1})
                session.commit()
                order.cancelled = 1
            if order.cancelled == 1:
                return error.error_order_cancelled (order_id)
            if order.paid == 1:
                buyer_id = order.user_id
                store_id = order.store_id
                total_price = order.total_price
                userStore = session.query(User_store).filter(User_store.store_id == store_id).all()
                seller_id = userStore[0].user_id
                session.query(User).filter(User.user_id == buyer_id).update({User.balance: User.balance + total_price})
                session.query(User).filter(User.user_id == seller_id).update({User.balance: User.balance - total_price})
                session.commit()
            session.query(New_order).filter(New_order.order_id == order_id).update({New_order.cancelled: 1})
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"
