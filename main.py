from typing import Optional
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import psycopg2
import datetime
import os
import bcrypt

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
        cursor.close()
        connect.close()
        return True
    except Exception as e:
        error_log(e)


@app.get("/user/get_id")
def get_id(login: str):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
    return cursor.fetchall()[0][0]


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


@app.put("/api/reports/{id}")
def update_report():
    try:
        pass
    except Exception as e:
        error_log(e)
