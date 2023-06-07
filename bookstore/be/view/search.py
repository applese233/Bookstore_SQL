from flask import Blueprint
from flask import request
from flask import jsonify
from be.model import search

bp_search = Blueprint("search", __name__, url_prefix="/search")


@bp_search.route("/book_info", methods=["POST"])
def book_info():
    book_id = request.json.get("book_id")
    isbn = request.json.get("isbn")
    s = search.Search()
    code, info = s.book_info(book_id, isbn)
    return jsonify({"book_info": info}), code


@bp_search.route("/fuzzy_search", methods=["POST"])
def fuzzy_search():
    term = request.json.get("term")
    store_id = request.json.get("store_id")
    page_size = request.json.get("page_size")
    page_id = request.json.get("page_id")
    s = search.Search()
    code, rst = s.fuzzy_search(term, store_id, page_size, page_id)
    return jsonify({"rst": rst}), code
