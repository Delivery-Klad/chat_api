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


@app.get("/auth")
def auth(login: str, password: str):
    try:
        connect, cursor = db_connect()
        cursor.execute("SELECT password FROM users WHERE login='{0}'".format(login))
        res = cursor.fetchall()[0][0].encode('utf-8')
        print(bcrypt.checkpw(password, res))
        return bcrypt.checkpw(password, res)
        """
        try:
            pass
        except IndexError:
            return JSONResponse(status_code=403)
        """
    except Exception as e:
        error_log(e)


@app.get("/api/reports")
def get_all_reports(sorted_by: Optional[str] = None):
    try:
        try:
            pass
        except IndexError:
            return JSONResponse(status_code=403)
    except Exception as e:
        error_log(e)


@app.put("/api/reports/{id}")
def update_report():
    try:
        pass
    except Exception as e:
        error_log(e)
