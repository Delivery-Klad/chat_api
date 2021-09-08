from Service.Variables import auth_handler
from database.Connect import db_connect
from datetime import datetime
from Service.Logger import error_log
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from rsa.transform import bytes2int, int2bytes
from Service.Models import *
from psycopg2 import Binary
from rsa import encrypt, PublicKey

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


def get_chat_id(name: str):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT id FROM chats WHERE name='{name}'")
        return cursor.fetchone()[0]
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


def get_chat_name(group_id: str):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT name FROM chats WHERE id='{group_id}'")
        return cursor.fetchone()[0]
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


def get_all_chats(login: str):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
        local_id = cursor.fetchone()[0]
        cursor.execute(f"SELECT to_id FROM messages WHERE from_id='{local_id}' ORDER BY date DESC")
        res = cursor.fetchall()
        temp = []
        for i in res:
            try:
                temp.index(i[0])
            except ValueError:
                temp.append(i[0])
        res = temp
        local_messages = []
        for i in res:
            cursor.execute(f"SELECT login FROM users WHERE id='{i}'")
            username = cursor.fetchone()[0]
            cursor.execute(f"(SELECT message1, read, id FROM messages WHERE to_id='{i}' AND from_id='{local_id}') "
                           f"UNION (SELECT message, read, id FROM messages WHERE to_id='{local_id}' AND from_id='{i}') "
                           f"ORDER BY id DESC LIMIT 1")
            data = cursor.fetchone()
            local_messages.append({"user_id": i, "username": username, "message": bytes2int(data[0]),
                                   "read": data[1]})
        cursor.execute(f"SELECT DISTINCT group_id FROM members WHERE user_id={local_id}")
        res = cursor.fetchall()
        for i in res:
            local_chat_id = i[0]
            cursor.execute(f"SELECT name FROM chats WHERE id='{local_chat_id}'")
            chat_name = cursor.fetchone()[0]
            cursor.execute(f"SELECT message, read FROM messages WHERE to_id='{local_id}' AND from_id LIKE "
                           f"'{local_chat_id}%' ORDER BY id DESC LIMIT 1")
            data = cursor.fetchone()
            if data is not None:
                local_messages.append({"user_id": local_chat_id, "username": chat_name, "message": bytes2int(data[0]),
                                       "read": data[1]})
        return local_messages
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


def get_chat_users(group_id: str, login: str):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT user_id FROM members WHERE user_id=(SELECT id FROM users WHERE login='{login}')"
                       f" AND group_id='{group_id}'")
        try:
            cursor.fetchall()[0][0]
        except IndexError:
            return None
        cursor.execute(f"SELECT user_id FROM members WHERE group_id='{group_id}'")
        return cursor.fetchall()
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


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
