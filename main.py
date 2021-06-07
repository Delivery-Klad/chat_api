from typing import Optional
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
import psycopg2
import datetime
import os
import bcrypt


class User(BaseModel):
    login: str
    password: str
    pubkey: str
    email: str


class Message(BaseModel):
    date: str
    sender: str
    destination: str
    message: bytes
    message1: bytes  # fix


app = FastAPI()


def db_connect():
    con = psycopg2.connect(
        host="ec2-54-247-107-109.eu-west-1.compute.amazonaws.com",
        database="de81d5uf5eagcd",
        user="guoucmhwdhynrf",
        port="5432",
        password="7720bda9eb76c990aee593f9064fa653136e3a047f989f53856b37549549ebe6")
    cur = con.cursor()
    return con, cur


def error_log(error):  # просто затычка, будет дописано
    try:
        print(error)
    except Exception as e:
        print(e)
        print("Возникла ошибка при обработке errorLog (Это вообще как?)")


"""
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    print(exc.detail)
    if "Not authenticated" in str(exc.detail):
        return PlainTextResponse(str(exc.detail), status_code=401)
    else:
        return PlainTextResponse(str(exc.detail), status_code=exc.status_code)
"""

"""
        try:
            pass
        except IndexError:
            return JSONResponse(status_code=403)
        """


@app.get("/create_tables")
def create_tables():
    connect, cursor = db_connect()
    try:
        # cursor.execute("DROP TABLE messages")
        # cursor.execute("DROP TABLE users")
        # cursor.execute("DROP TABLE chats")
        # debug(cursor)
        cursor.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER,'
                       'login TEXT,'
                       'password TEXT,'
                       'pubkey TEXT,'
                       'email TEXT)')
        cursor.execute('CREATE TABLE IF NOT EXISTS chats(id TEXT,'
                       'name TEXT,'
                       'owner INTEGER)')
        cursor.execute('CREATE TABLE IF NOT EXISTS messages(date TIMESTAMP,'
                       'from_id TEXT,'
                       'to_id TEXT,'
                       'message BYTEA,'
                       'message1 BYTEA,'
                       'file TEXT,'
                       'read INTEGER)')
        connect.commit()
        cursor.execute('SELECT * FROM messages')
        print(cursor.fetchall())
        cursor.close()
        connect.close()
        return True
    except Exception as e:
        error_log(e)


@app.get("/auth")
def auth(login: str, password: str):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT password FROM users WHERE login='{login}'")
        return bcrypt.checkpw(password.encode('utf-8'), cursor.fetchall()[0][0].encode('utf-8'))
    except IndexError:
        return None
    except Exception as e:
        error_log(e)


@app.get("/user/can_use_login")
def can_use_login(login: str):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
    return cursor.fetchall()[0][0]


@app.get("/user/get_id")
def get_id(login: str):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
    return cursor.fetchall()[0][0]


@app.get("/user/get_nickname")
def get_nickname(id: int):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT login FROM users WHERE id={id}")
        return cursor.fetchall()[0][0]
    except IndexError:
        return None


@app.get("/user/get_pubkey")
def get_pubkey(id: str):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT pubkey FROM users WHERE id={id}")
    return cursor.fetchall()[0][0]


@app.get("/user/get_groups")
def get_groups(user_id: int):
    connect, cursor = db_connect()
    groups = []
    cursor.execute("SELECT name FROM chats")
    res = cursor.fetchall()
    for el in res:
        cursor.execute(f"SELECT COUNT(id) FROM {el[0]} WHERE id='{user_id}'")
        tmp = cursor.fetchall()[0][0]
        if tmp == 1:
            groups.append(el[0])
    return groups


@app.post("/user/create")
def create_user(user: User):
    try:
        connect, cursor = db_connect()
        cursor.execute("SELECT MAX(id) FROM users")
        max_id = cursor.fetchall()[0][0]
        if max_id is not None:
            max_id += 1
        else:
            max_id = 0
        cursor.execute(f"INSERT INTO users VALUES ({max_id},'{user.login}','{user.password}','{user.pubkey}',"
                       f"'{user.email}')")
        return JSONResponse(status_code=200)
    except Exception as e:
        error_log(e)
        return JSONResponse(status_code=404)


@app.post("/messages/send")
def send_message(message: Message):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"INSERT INTO messages VALUES (to_timestamp('{message.date}', 'dd-mm-yy hh24:mi:ss'),"
                       f"'{message.sender}','{message.destination}', {message.message},"
                       f"{message.message1}, '-', 0)")
        connect.commit()
        return JSONResponse(status_code=200)
    except Exception as e:
        error_log(e)
        return JSONResponse(status_code=404)


@app.get("/messages/get")
def get_message(user_id: int, chat_id: int):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT * FROM messages WHERE to_id='{user_id}' AND from_id='{chat_id}' AND NOT from_id LIKE 'g%' "
                   "ORDER BY date")
    res = cursor.fetchall()
    cursor.execute(f"SELECT * FROM messages WHERE to_id='{chat_id}' AND from_id='{user_id}' AND NOT from_id LIKE 'g%' "
                   "ORDER BY date")
    res += cursor.fetchall()
    cursor.execute(f"UPDATE messages SET read=1 WHERE to_id='{user_id}' AND from_id LIKE '{chat_id}' AND read=0")
    connect.commit()
    res.sort()
    print(res)
    print(type(res))
    return res


@app.put("/api/reports/{id}")
def update_report():
    try:
        pass
    except Exception as e:
        error_log(e)
