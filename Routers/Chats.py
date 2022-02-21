from datetime import datetime

from psycopg2 import Binary
from rsa import encrypt, PublicKey
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from Service.Variables import auth_handler
from database.Connect import db_connect
from Service.Logger import error_log
from Service.Models import *
from Service.Methods import get_chat_id, get_chat_name, get_all_chats, get_chat_users

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/")
async def chats_get_handler_wo_header(chat_id: Optional[bool] = None, chat_name: Optional[bool] = None,
                                      name: Optional[str] = None, id: Optional[str] = None):
    if chat_id:
        return get_chat_id(name) if name is not None else JSONResponse(status_code=500)
    if chat_name:
        return get_chat_name(id) if id is not None else JSONResponse(status_code=500)


@router.put("/")
async def chats_get_handler_with_header(all: Optional[bool] = None, chat_users: Optional[bool] = None,
                                        id: Optional[str] = None, login=Depends(auth_handler.decode)):
    if all:
        return get_all_chats(login)
    if chat_users:
        return get_chat_users(id, login) if id is not None else JSONResponse(status_code=500)


@router.post("/")
async def create_chat(chat: Group, owner=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT COUNT(name) FROM chats WHERE name='{chat.name}'")
        if cursor.fetchone()[0] != 0:
            return None
        cursor.execute("SELECT COUNT(*) FROM chats")
        max_id = int(cursor.fetchone()[0]) + 1
        cursor.execute(f"SELECT id FROM users WHERE login='{owner}'")
        owner_id = cursor.fetchone()[0]
        cursor.execute(f"INSERT INTO chats VALUES ('g{max_id}', '{chat.name}', {owner_id})")
        cursor.execute(f"INSERT INTO members VALUES('g{max_id}', {owner_id})")
        connect.commit()
        cursor.execute(f"SELECT pubkey FROM users WHERE id={owner_id}")
        pubkey = cursor.fetchone()[0].split(", ")
        pubkey = PublicKey(int(pubkey[0]), int(pubkey[1]))
        date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
        msg = Binary(encrypt("Chat created".encode("utf-8"), pubkey))
        cursor.execute(f"INSERT INTO messages(date, from_id, to_id, message, message1, read) VALUES (to_timestamp("
                       f"'{date}', 'dd-mm-yy hh24:mi:ss'),'g{max_id}_0','{owner_id}',{msg},{msg}, 0)")
        connect.commit()
        return True
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.patch("/")
async def chat_invite(invite: Invite, user=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT login FROM users WHERE id=(SELECT owner FROM chats WHERE name='{invite.name}')")
        if cursor.fetchone()[0] == user:
            cursor.execute(f"SELECT id FROM chats WHERE name='{invite.name}'")
            chat_id = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM members WHERE group_id='{chat_id}' AND user_id={invite.user}")
            if cursor.fetchone()[0] != 0:
                return False
            cursor.execute(f"SELECT COUNT(*) FROM users WHERE id={invite.user}")
            if cursor.fetchone()[0] == 0:
                return False
            cursor.execute(f"INSERT INTO members VALUES({chat_id},{invite.user})")
            connect.commit()
            cursor.execute(f"SELECT pubkey FROM users WHERE id={invite.user}")
            pubkey = cursor.fetchone()[0].split(", ")
            pubkey = PublicKey(int(pubkey[0]), int(pubkey[1]))
            message = encrypt("You have been invited to a group".encode("utf-8"), pubkey)
            date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
            msg = Binary(message)
            cursor.execute(f"INSERT INTO messages(date, from_id, to_id, message, message1, read) VALUES (to_timestamp("
                           f"'{date}', 'dd-mm-yy hh24:mi:ss'),'{chat_id}_0','{invite.user}',{msg},{msg}, 0)")
            connect.commit()
            return True
        return False
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.delete("/")
async def chat_kick(invite: Invite, user=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT login FROM users WHERE id=(SELECT owner FROM chats WHERE name='{invite.name}')")
        if cursor.fetchone()[0] == user:
            cursor.execute(f"DELETE FROM members WHERE user_id={invite.user} AND group_id=(SELECT "
                           f"id FROM chats WHERE name='{invite.name}')")
            connect.commit()
            return True
        return False
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()
