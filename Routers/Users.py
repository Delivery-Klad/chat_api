import bcrypt
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from database.Connect import db_connect
from Service.Variables import auth_handler
from Service.Models import *
from Service.Methods import get_random, get_id, find_user, get_nickname, get_pubkey, get_groups

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


@router.put("/")
async def update_user_pubkey(pubkey: NewPubkey, login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"UPDATE users SET pubkey='{pubkey.pubkey}' WHERE login='{login}'")
        connect.commit()
        return True
    finally:
        cursor.close()
        connect.close()


@router.patch("/")
async def update_user(data: NewPassword, login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT password FROM users WHERE login='{login}'")
        res = bcrypt.checkpw(data.old_password.encode('utf-8'), cursor.fetchone()[0].encode('utf-8'))
        if res:
            cursor.execute(f"UPDATE users SET password='{data.new_password}' WHERE login='{login}'")
            connect.commit()
            return True
        return False
    finally:
        cursor.close()
        connect.close()


@router.delete("/")
async def remove_data_request(login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
    user_id = cursor.fetchone()[0]
    cursor.execute(f"UPDATE users SET login='Deleted_{user_id}', password='None', pubkey='None', email='None' "
                   f"WHERE login='{login}'")
    connect.commit()
    cursor.close()
    connect.close()
    return True
