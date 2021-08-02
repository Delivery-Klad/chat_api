from sqlalchemy import Column, Integer, Text, BigInteger, LargeBinary, TIMESTAMP
from database.database import DataBase


class Users(DataBase):
    __tablename__ = "users"
    id = Column(BigInteger, nullable=False, unique=True, primary_key=True, index=True, autoincrement=True)
    login = Column(Text, nullable=False, unique=True)
    password = Column(Text, nullable=False)
    pubkey = Column(Text, nullable=False)
    email = Column(Text, nullable=False)
    last_activity = Column(TIMESTAMP)


class Chats(DataBase):
    __tablename__ = "chats"
    id = Column(Text, nullable=False, unique=True)
    name = Column(Text, nullable=False, unique=True)
    owner = Column(BigInteger, nullable=False)


class Messages(DataBase):
    __tablename__ = "messages"
    id = Column(BigInteger, nullable=False, unique=True, primary_key=True, index=True, autoincrement=True)
    date = Column(TIMESTAMP, nullable=False)
    from_id = Column(Text, nullable=False)
    to_id = Column(Text, nullable=False)
    message = Column(LargeBinary, nullable=False)
    message1 = Column(LargeBinary)
    read = Column(Integer, nullable=False)


class Links(DataBase):
    __tablename__ = "links"
    id = Column(BigInteger, nullable=False, unique=True, primary_key=True, index=True, autoincrement=True)
    longlink = Column(Text, nullable=False)
