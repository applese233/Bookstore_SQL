import jwt
import time
import logging
from typing import Tuple
from be.model import error
from be.model.database import getDbSession, getDatabaseBase
from sqlalchemy import Column, String, Text, Integer, Date, create_engine
from sqlalchemy.exc import SQLAlchemyError

# encode a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }


def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    return encoded.encode("utf-8").decode("utf-8")


# decode a JWT to a json string like:
#   {
#       "user_id": [user name],
#       "terminal": [terminal code],
#       "timestamp": [ts]} to a JWT
#   }
def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded

Base = getDatabaseBase()
class User(Base):
    __tablename__ = "user"
    user_id = Column(Text, primary_key = True, unique = True, nullable = False)
    password = Column(Text, nullable = False)
    balance = Column(Integer, nullable = False)
    token = Column(Text)
    terminal = Column(Text)

    token_lifetime: int = 3600  # 3600 second

    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            if db_token != token:
                return False
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:
            logging.error(str(e))
            return False

    def register(self, user_id: str, password: str):
        try:
            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            session = getDbSession()
            session.add(User(user_id = user_id, password = password, balance = 0, token = token, terminal = terminal))
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return error.error_exist_user_id(user_id)
        except BaseException as e:
            print("register" + str(e))
            return 530, "{}".format(str(e))
        return 200, "ok"

    def check_token(self, user_id: str, token: str) -> Tuple[int, str]:
        session = getDbSession()
        result = session.query(User).filter(User.user_id == user_id).all()
        if len (result) == 0:
            return error.error_authorization_fail()
        db_token = result[0].token
        if not self.__check_token(user_id, db_token, token):
            return error.error_authorization_fail()
        return 200, "ok"

    def check_password(self, user_id: str, password: str) -> Tuple[int, str]:
        session = getDbSession()
        result = session.query(User).filter(User.user_id == user_id).all()
        if len (result) == 0:
            return error.error_authorization_fail()
        if password != result[0].password:
            return error.error_authorization_fail()
        return 200, "ok"

    def login(self, user_id: str, password: str, terminal: str) -> Tuple[int, str, str]:
        token = ""
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message, ""

            token = jwt_encode(user_id, terminal)
            session = getDbSession()
            result = session.query(User).filter(User.user_id == user_id).all()
            if len(result) == 0:
                return error.error_authorization_fail() + ("", )
            session.query(User).filter(User.user_id == user_id).update({User.token: token, User.terminal: terminal})
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e)), ""
        except BaseException as e:
            return 530, "{}".format(str(e)), ""
        return 200, "ok", token

    def logout(self, user_id: str, token: str) -> bool:
        try:
            code, message = self.check_token(user_id, token)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)

            session = getDbSession()
            result = session.query(User).filter(User.user_id == user_id).all()
            if len(result) == 0:
                return error.error_authorization_fail() + ("", )
            session.query(User).filter(User.user_id == user_id).update({User.token: dummy_token, User.terminal: terminal})
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def unregister(self, user_id: str, password: str) -> Tuple[int, str]:
        try:
            code, message = self.check_password(user_id, password)
            if code != 200:
                return code, message
            session = getDbSession()
            result = session.query(User).filter(User.user_id == user_id).all()
            if len(result) == 0:
                return error.error_authorization_fail()
            session.query(User).filter(User.user_id == user_id).delete()
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        try:
            code, message = self.check_password(user_id, old_password)
            if code != 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            session = getDbSession()
            result = session.query(User).filter(User.user_id == user_id).all()
            if len(result) == 0:
                return error.error_authorization_fail()
            session.query(User).filter(User.user_id == user_id).update({User.password: new_password, User.token: token, User.terminal: terminal})
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            return 528, "{}".format(str(e))
        except BaseException as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

def getBalance (user_id: str) -> int:
    session = getDbSession()
    result = session.query(User).filter(User.user_id == user_id).all()
    if len(result) == 0:
        return -1
    return result[0].balance