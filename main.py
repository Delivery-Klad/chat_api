from typing import Optional
from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import psycopg2
import datetime
import os

app = FastAPI()


def db_connect():
    con = psycopg2.connect(
        host="ec2-52-213-167-210.eu-west-1.compute.amazonaws.com",
        database=os.environ.get("DB"),
        user=os.environ.get("DB_user"),
        port="5432",
        password=os.environ.get("DB_pass")
    )
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
