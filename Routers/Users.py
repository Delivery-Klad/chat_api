from Service.Variables import auth_handler
from database.Connect import db_connect
from Service.Logger import error_log
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from Service.Models import *
import bcrypt

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/")
async def user_get_handler(random: Optional[bool] = None, user_id: Optional[bool] = None, find: Optional[bool] = None,
                           name: Optional[bool] = None, pubkey: Optional[bool] = None, groups: Optional[bool] = None,
                           login: Optional[str] = None, id: Optional[int] = None):
    if random:
        return get_random()
    elif user_id:
        return get_id(login) if login is not None else JSONResponse(status_code=500)
    elif find:
        return find_user(login) if login is not None else JSONResponse(status_code=500)
    elif name:
        return get_nickname(id) if id is not None else JSONResponse(status_code=500)
    elif pubkey:
        return get_pubkey(id) if id is not None else JSONResponse(status_code=500)
    elif groups:
        return get_groups(id) if id is not None else JSONResponse(status_code=500)


def get_random():
    connect, cursor = db_connect()
    try:
        res_dict = []
        cursor.execute(f"SELECT id, login, last_activity FROM users WHERE login NOT LIKE 'Service' "
                       f"ORDER BY random() LIMIT 30")
        res = cursor.fetchall()
        for i in range(len(res)):
            res_dict.append({"id": res[i][0], "login": res[i][1], "last_activity": res[i][2]})
        return res_dict
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


def get_id(login: str):
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


def find_user(login: str):
    connect, cursor = db_connect()
    res_dict = []
    try:
        if login[-3:] == "_gr":
            cursor.execute(f"SELECT users.id, users.login, users.last_activity FROM members JOIN users ON "
                           f"members.user_id = users.id WHERE group_id=(SELECT id FROM chats WHERE name='{login}')")
            res = cursor.fetchall()
            for i in range(len(res)):
                res_dict.append({"id": res[i][0], "login": res[i][1], "last_activity": res[i][2]})
        else:
            cursor.execute(f"SELECT id, login, last_activity FROM users WHERE login LIKE '%{login}%' AND login NOT LIKE"
                           f" 'Service'")
            res = cursor.fetchall()
            for i in range(len(res)):
                res_dict.append({"id": res[i][0], "login": res[i][1], "last_activity": res[i][2]})
        return res_dict
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


def get_nickname(id: int):
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


def get_pubkey(id: int):
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


def get_groups(user_id: int):
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


@router.put("/")
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


@router.patch("/")
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


@router.delete("/")
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
