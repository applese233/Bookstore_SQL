import pytest
from typing import List

from fe.access.buyer import Buyer
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.book import Book

from be.model.user import getBalance

import uuid


class TestPayment:
    seller_id: str
    store_id: str
    buyer_id: str
    password:str
    buy_book_info_list: List[Book]
    total_price: int
    order_id: str
    buyer: Buyer

    @pytest.fixture(autouse=True)
    def pre_run_initialization(self):
        self.seller_id = "test_payment_seller_id_{}".format(str(uuid.uuid1()))
        self.store_id = "test_payment_store_id_{}".format(str(uuid.uuid1()))
        self.buyer_id = "test_payment_buyer_id_{}".format(str(uuid.uuid1()))
        self.password = self.seller_id
        gen_book = GenBook(self.seller_id, self.store_id)
        ok, buy_book_id_list = gen_book.gen(non_exist_book_id=False, low_stock_level=False, max_book_count=5)
        self.buy_book_info_list = gen_book.buy_book_info_list
        assert ok
        b = register_new_buyer(self.buyer_id, self.password)
        self.buyer = b
        code, self.order_id = b.new_order(self.store_id, buy_book_id_list)
        assert code == 200
        self.total_price = 0
        for item in self.buy_book_info_list:
            book: Book = item[0]
            num = item[1]
            if book.price is None:
                continue
            else:
                self.total_price = self.total_price + book.price * num
        yield

    def test_ok(self):
        preBalance = getBalance (self.buyer_id)
        code = self.buyer.add_funds(self.total_price)
        postBalance = getBalance (self.buyer_id)
        assert code == 200
        assert postBalance - preBalance == self.total_price

        preBalance = getBalance (self.buyer_id)
        preSellerBalance = getBalance (self.seller_id)
        code = self.buyer.payment(self.order_id)
        postBalance = getBalance (self.buyer_id)
        postSellerBalance = getBalance (self.seller_id)
        assert code == 200
        assert preBalance - postBalance == self.total_price
        assert postSellerBalance - preSellerBalance == self.total_price

    def test_authorization_error(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        self.buyer.password = self.buyer.password + "_x"
        code = self.buyer.payment(self.order_id)
        assert code != 200

    def test_not_suff_funds(self):
        code = self.buyer.add_funds(self.total_price - 1)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 519

    def test_repeat_pay(self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.payment(self.order_id)
        assert code == 200

        code = self.buyer.payment(self.order_id)
        assert code == 520

    def test_pay_after_cancel (self):
        code = self.buyer.add_funds(self.total_price)
        assert code == 200
        code = self.buyer.cancel_order (self.order_id)
        assert code == 200

        code = self.buyer.payment(self.order_id)
        assert code == 521
