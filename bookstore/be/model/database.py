from sqlalchemy.orm import sessionmaker, session, declarative_base
from sqlalchemy import create_engine, Column, Text, Integer, DateTime, Boolean

class Database:
    def __init__ (self):
        self.engine = create_engine("postgresql://postgres:20020318@127.0.0.1:5432/bookstore", pool_size = 8, pool_recycle = 60 * 30)
        self.Dbsession = sessionmaker(bind = self.engine)
        self.session = self.Dbsession()
        self.base = declarative_base()
    
    def getEngine(self):
        return self.engine

    def getSession(self):
        return self.session

    def getBase(self):
        return self.base

    def __del__(self):
        self.session.close()

database_instance: Database = Database()

def getDatabaseBase():
    global database_instance
    return database_instance.getBase()

def getDbSession() -> session:
    global database_instance
    return database_instance.getSession()

Base = getDatabaseBase()

def init_database():
    global database_instance
    engine = database_instance.getEngine()
    database_instance.getBase().metadata.create_all(engine)
    
class User_store(Base):
    __tablename__ = "user_store"

    user_id = Column(Text, primary_key = True, nullable = False)
    store_id = Column(Text, primary_key = True, nullable = False)

class Store(Base):
    __tablename__ = "store"

    store_id = Column(Text, primary_key = True, nullable = False)
    book_id = Column(Text, primary_key = True, nullable = False)
    book_info = Column(Text, nullable = False)
    stock_level = Column(Integer, nullable = False)

class New_order(Base):
    __tablename__ = "new_order"

    order_id = Column(Text, primary_key = True, unique = True, nullable = False)
    user_id = Column(Text, nullable = False)
    store_id = Column(Text, nullable = False)
    order_time = Column(DateTime, nullable = False)
    total_price = Column(Integer, nullable = False)
    paid = Column(Boolean, nullable = False)
    cancelled = Column(Boolean, nullable = False)
    delivered = Column(Boolean, nullable = False)

class New_order_detail(Base):
    __tablename__ = "new_order_detail"

    order_id = Column(Text, primary_key = True, nullable = False)
    book_id = Column(Text, primary_key = True, nullable = False)
    count = Column(Integer, nullable = False)
    price = Column(Integer, nullable = False)

    def Formulate(self):
        return {"order_id": self.order_id, "book_id": self.book_id, "count": self.count, "price": self.price}

def user_id_exist(user_id) -> bool:
    from be.model.user import User
    result = getDbSession().query(User).filter(User.user_id == user_id).all()
    if len(result) == 0:
        return False
    else:
        return True
    
def book_id_exist(store_id, book_id):
    result = getDbSession().query(Store).filter(Store.store_id == store_id, Store.book_id == book_id).all()
    if len(result) == 0:
        return False
    else:
        return True

def store_id_exist(store_id):
    result = getDbSession().query(User_store).filter(User_store.store_id == store_id).all()
    if len(result) == 0:
        return False
    else:
        return True