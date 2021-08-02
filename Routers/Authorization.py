from Service.Variables import auth_handler
from database.Connect import db_connect
from Service.Logger import error_log
from Service.Models import *
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import bcrypt

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", tags=["Auth"])
async def auth_login(data: Auth):
    connect, cursor = db_connect()
    try:
        if data.login.lower() == "deleted":
            return False
        cursor.execute(f"SELECT password FROM users WHERE login='{data.login}'")
        if bcrypt.checkpw(data.password.encode("utf-8"), cursor.fetchone()[0].encode("utf-8")):
            date = datetime.utcnow().strftime("%d-%m-%Y %H:%M:%S")
            cursor.execute(f"UPDATE users SET last_activity=to_timestamp('{date}','dd-mm-yy hh24:mi:ss') WHERE "
                           f"login='{data.login}'")
            connect.commit()
            token = auth_handler.encode(data.login)
            return token
        else:
            return False
    except IndexError:
        return None
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.post("/register", tags=["Auth"])
async def auth_register(user: User):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT id FROM users WHERE login='{user.login}'")
        try:
            cursor.fetchone()[0]
        except IndexError:
            if user.login.lower() == "deleted":
                return False
            date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
            cursor.execute(f"INSERT INTO users(login, password, pubkey, email, last_activity) VALUES ('{user.login}',"
                           f"'{user.password}','{user.pubkey}','{user.email}', to_timestamp('{date}',"
                           f"'dd-mm-yy hh24:mi:ss'))")
            connect.commit()
            return True
        return False
    except Exception as e:
        error_log(e)
        return JSONResponse(status_code=500)
    finally:
        cursor.close()
        connect.close()
