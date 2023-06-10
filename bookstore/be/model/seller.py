from typing import Tuple
from sqlalchemy.exc import SQLAlchemyError
from be.model import error
from be.model.database import user_id_exist, book_id_exist, store_id_exist, getDbSession, User_store, Store, New_order, New_order_detail

class Seller():

    def add_book(self, user_id: str, store_id: str, book_id: str, book_json_str: str, stock_level: int):
        try:
            if not user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            session = getDbSession()
            session.add(Store(store_id = store_id, book_id = book_id, book_info = book_json_str, stock_level = stock_level))
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
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
            session = getDbSession()
            session.query(Store).filter(Store.store_id == store_id, Store.book_id == book_id).update({Store.stock_level: Store.stock_level + add_stock_level})
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
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
            session = getDbSession()
            session.add(User_store(store_id = store_id, user_id = user_id))
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def deliver_order(self, order_id: str) -> Tuple[int, str]:
        try:
            session = getDbSession()
            order = session.query(New_order).filter(New_order.order_id == order_id).all()
            if len(order) == 0:
                return error.error_invalid_order_id(order_id)
            if order[0].paid == 0:
                return error.error_order_not_paid(order_id)
            if order[0].cancelled == 1:
                return error.error_order_already_cancelled(order_id)
            if order[0].delivered == 1:
                return error.error_order_already_delivered(order_id)
            store_id = order[0].store_id
            if not store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            detailed_order = session.query(New_order_detail).filter(New_order_detail.order_id == order_id).all()
            if len(detailed_order) == 0:
                return error.error_invalid_order_id(order_id)
            for each in detailed_order:
                book_id = each.book_id
                count = each.count
                if not book_id_exist(store_id, book_id):
                    return error.error_non_exist_book_id(book_id)
                result = session.query(Store).filter(Store.store_id == store_id, Store.book_id == book_id, Store.stock_level >= count).all()
                if len(result) == 0:
                    return error.error_stock_level_low(book_id)
                session.query(Store).filter(Store.store_id == store_id, Store.book_id == book_id).update({Store.stock_level: Store.stock_level - count})
                session.commit()
            result = session.query(New_order).filter(New_order.order_id == order_id).all()
            if len(result) == 0:
                return error.error_invalid_order_id(order_id)
            session.query(New_order).filter(New_order.order_id == order_id).update({New_order.delivered: 1})
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            print(str(e))
            return 530, "{}".format(str(e))
        return 200, "ok"
