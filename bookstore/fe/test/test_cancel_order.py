import pytest
from datetime import datetime, timedelta

from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book

from be.model.collection import Collection
from be.model.user import getBalance

import uuid


class TestCancelOrder:
    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_cancel_order_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_cancel_order_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_cancel_order_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        self.buyer = register_new_buyer(self.buyer_id, self.password)
        self.gen_book = GenBook(self.seller_id, self.store_id)
        yield

    def test_ok(self):
        ok, buy_book_id_list = self.gen_book.gen(non_exist_book_id=False, low_stock_level=False)
        buy_book_info_list = self.gen_book.buy_book_info_list
        assert ok
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200

        total_price = 0
        for item in buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            else:
                total_price += book.price * num

        code = self.buyer.add_funds (total_price)
        assert code == 200
        sellerPreBalance = getBalance (self.seller_id)
        code = self.buyer.payment (order_id)
        assert code == 200
        code = self.buyer.cancel_order (order_id)
        assert code == 200
        assert getBalance (self.buyer_id) == total_price
        assert getBalance (self.seller_id) == sellerPreBalance

    def test_repeat_cancel(self):
        ok, buy_book_id_list = self.gen_book.gen(non_exist_book_id=False, low_stock_level=False)
        assert ok
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        code = self.buyer.cancel_order (order_id)
        assert code == 200
        code = self.buyer.cancel_order (order_id)
        assert code == 521

    def test_outdate_cancel (self):
        ok, buy_book_id_list = self.gen_book.gen(non_exist_book_id=False, low_stock_level=False)
        assert ok
        curDateTime = datetime.now()
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        orderCollection = Collection ("new_order").collection
        orderCollection.update_one ({"order_id": order_id}, {"$set": {"order_time": curDateTime - timedelta (minutes=15)}})
        code = self.buyer.cancel_order (order_id)
        assert code == 521

    def test_outdate_cancel_payment (self):
        ok, buy_book_id_list = self.gen_book.gen(non_exist_book_id=False, low_stock_level=False)
        buy_book_info_list = self.gen_book.buy_book_info_list
        assert ok
        total_price = 0
        for item in buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            else:
                total_price += book.price * num
        code = self.buyer.add_funds (total_price)
        curDateTime = datetime.now()
        code, order_id = self.buyer.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        orderCollection = Collection ("new_order").collection
        orderCollection.update_one ({"order_id": order_id}, {"$set": {"order_time": curDateTime - timedelta (minutes=15)}})
        code = self.buyer.payment (order_id)
        assert code == 521