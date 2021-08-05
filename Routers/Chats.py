from Service.Variables import auth_handler
from database.Connect import db_connect
from Service.Logger import error_log
from fastapi import APIRouter, Depends
from rsa.transform import bytes2int
from Service.Models import *

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/get_all")
async def get_all_chats(login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
        local_id = cursor.fetchone()[0]
        # SELECT DISTINCT to_id FROM messages WHERE from_id='{local_id}'
        cursor.execute(f"SELECT DISTINCT to_id FROM (SELECT to_id FROM messages WHERE from_id='{local_id}'"
                       f"ORDER BY date) AS msgs")
        res = cursor.fetchall()
        print(res)
        local_messages = {}
        local_message_id = 0
        local_messages.update({"count": len(res)})
        for i in res:
            cursor.execute(f"SELECT login FROM users WHERE id='{i[0]}'")
            username = cursor.fetchone()[0]
            cursor.execute(f"SELECT message1 FROM messages WHERE to_id='{i[0]}' AND from_id='{local_id}' "
                           f"ORDER BY id DESC LIMIT 1")  # подправить
            local_messages.update({f"item_{local_message_id}": {"user_id": i[0], "username": username,
                                                                "message": bytes2int(cursor.fetchone()[0])}})
            local_message_id += 1
        cursor.execute(f"SELECT DISTINCT from_id FROM messages WHERE from_id LIKE 'g%_{local_id}'")
        res = cursor.fetchall()
        local_messages.update({"count": local_messages['count'] + len(res)})
        for i in res:
            local_chat_id = i[0].split('_')[0]
            cursor.execute(f"SELECT name FROM chats WHERE id='{local_chat_id}'")
            chat_name = cursor.fetchone()[0]
            cursor.execute(f"SELECT message FROM messages WHERE to_id='{local_id}' AND from_id LIKE '{local_chat_id}%' "
                           f"ORDER BY id DESC LIMIT 1")
            local_messages.update({f"item_{local_message_id}": {"user_id": local_chat_id, "username": chat_name,
                                                                "message": bytes2int(cursor.fetchone()[0])}})
            local_message_id += 1
        return local_messages
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.post("/create")
async def create_chat(chat: Group, owner=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema NOT IN ("
                       "'information_schema', 'pg_catalog') AND table_schema IN('public', 'myschema');")
        if ('{0}'.format(chat.name),) in cursor.fetchall():
            return None
        cursor.execute("SELECT COUNT(*) FROM chats")
        max_id = int(cursor.fetchone()[0]) + 1
        cursor.execute(f"SELECT id FROM users WHERE login='{owner}'")
        owner_id = cursor.fetchone()[0]
        cursor.execute(f"INSERT INTO chats VALUES ('g{max_id}', '{chat.name}', {owner_id})")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {chat.name}(id BIGINT REFERENCES users (id))")
        connect.commit()
        cursor.execute(f"INSERT INTO {chat.name} VALUES({owner_id})")
        connect.commit()
        return True
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.get("/get_id")
async def get_chat_id(name: str):
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


@router.get("/get_name")
async def get_chat_name(group_id: str):
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


@router.get("/get_users")
async def get_chat_users(group_id: str, login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT name FROM chats WHERE id='{group_id}'")
        group_name = cursor.fetchone()[0]
        cursor.execute(f"SELECT id FROM {group_name} WHERE id=(SELECT id FROM users WHERE login='{login}')")
        try:
            cursor.fetchall()[0][0]
        except IndexError:
            return None
        cursor.execute(f"SELECT id FROM {group_name}")
        return cursor.fetchall()
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.post("/invite")
async def chat_invite(invite: Invite, user=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT login FROM users WHERE id='(SELECT owner FROM chats WHERE name='{invite.name}')'")
        if cursor.fetchone()[0] == user:
            cursor.execute(f"INSERT INTO {invite.name} VALUES({invite.user})")
            connect.commit()
            return True
        return False
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


@router.post("/kick")
async def chat_kick(invite: Invite, user=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT login FROM users WHERE id='(SELECT owner FROM chats WHERE name='{invite.name}')'")
        if cursor.fetchone()[0] == user:
            cursor.execute(f"DELETE FROM {invite.name} WHERE id={invite.user}")
            connect.commit()
            return True
        return False
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()
