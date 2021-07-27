from database.Variables import auth_handler
from database.Connect import db_connect
from Service.Logger import error_log
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from Service.Models import *
import bcrypt

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/get_random")  # переписать запрос
async def get_random():
    connect, cursor = db_connect()
    try:
        res_dict = {}
        cursor.execute(f"SELECT id, login, last_activity FROM users ORDER BY random() LIMIT 30")
        res = cursor.fetchall()
        res_dict.update({"count": len(res)})
        for i in range(len(res)):
            res_dict.update({f"user_{i}": {"id": res[i][0], "login": res[i][1], "last_activity": res[i][2]}})
        return res_dict
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.get("/find")
async def find_user(login: str):
    connect, cursor = db_connect()
    try:
        res_dict = {}
        try:
            if login[-3:] == "_gr":
                cursor.execute(f"SELECT users.id, users.login, users.last_activity FROM {login} JOIN users ON "
                               f"{login}.id = users.id")
                res = cursor.fetchall()
                res_dict.update({"count": len(res)})
                for i in range(len(res)):
                    res_dict.update({f"user_{i}": {"id": res[i][0], "login": res[i][1], "last_activity": res[i][2]}})
                return res_dict
        except Exception as e:
            print(e)
        cursor.execute(f"SELECT id, login, last_activity FROM users WHERE login LIKE '%{login}%'")
        res = cursor.fetchall()
        res_dict.update({"count": len(res)})
        for i in range(len(res)):
            res_dict.update({f"user_{i}": {"id": res[i][0], "login": res[i][1], "last_activity": res[i][2]}})
        return res_dict
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.get("/get_id")
async def get_id(login: str):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
        return cursor.fetchone()[0]
    except IndexError:
        return None
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.get("/get_nickname")
async def get_nickname(id: int):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT login FROM users WHERE id={id}")
        return cursor.fetchone()[0]
    except IndexError:
        return None
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.get("/get_pubkey")
async def get_pubkey(id: str):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT pubkey FROM users WHERE id={id}")
        return cursor.fetchone()[0]
    except IndexError:
        return None
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.get("/get_groups")
async def get_groups(user_id: int):
    connect, cursor = db_connect()
    try:
        groups = []
        cursor.execute("SELECT name FROM chats")
        for el in cursor.fetchall():
            cursor.execute(f"SELECT COUNT(id) FROM {el[0]} WHERE id={user_id}")
            if cursor.fetchone()[0] == 1:
                groups.append(el[0])
        return groups
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.put("/update_pubkey")
async def create_user(pubkey: NewPubkey, login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"UPDATE users SET pubkey='{pubkey.pubkey}' WHERE login='{login}'")
        connect.commit()
        return True
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.put("/update_password")
async def create_user(data: NewPassword, login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        try:
            cursor.execute(f"SELECT password FROM users WHERE login='{login}'")
            res = bcrypt.checkpw(data.old_password.encode('utf-8'), cursor.fetchone()[0].encode('utf-8'))
        except IndexError:
            res = None
        if res:
            cursor.execute(f"UPDATE users SET password='{data.new_password}' WHERE login='{login}'")
            connect.commit()
            return True
        elif res is None:
            return None
        else:
            return False
    except Exception as e:
        error_log(e)
        return JSONResponse(status_code=500)
    finally:
        cursor.close()
        connect.close()


@router.delete("/remove")
async def remove_data_request(login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"UPDATE users SET login='Deleted', password='None', pubkey='None', email='None' "
                       f"WHERE login='{login}'")
        connect.commit()
        return True
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()
