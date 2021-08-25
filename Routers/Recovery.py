from database.Connect import db_connect
from Service.Methods import send_mail
from Service.Logger import error_log
from Service.Models import *
from fastapi import APIRouter
import random

router = APIRouter(prefix="/recovery", tags=["Recovery"])
recovery_codes = []


@router.get("/")
async def recovery_send(login: str):
    global recovery_codes
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT email FROM users WHERE login='{login}'")
        code = random.randint(100000, 999999)
        recovery_codes.append(f"{login}_{code}")
        print(recovery_codes)
        return send_mail(cursor.fetchone()[0], "Recovery code", "Your code: {0}".format(code))
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.post("/")
async def recovery_validate(data: ResetPassword):
    global recovery_codes
    for i in recovery_codes:
        connect, cursor = db_connect()
        try:
            res = i.split(data.login)
            res.pop(0)
            print(f"{data.code} {res[0][1:]}")
            if data.code == res[0][1:]:
                if data.password is not None:
                    cursor.execute(f"UPDATE users SET password='{data.password}' WHERE login='{data.login}'")
                    connect.commit()
                return True
            return False
        except Exception as e:
            print(e)
            return None
        finally:
            cursor.close()
            connect.close()
    return False
