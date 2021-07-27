from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from Routers import API, Services, Files
from database.Variables import auth_handler
from database.Connect import db_connect
from Service.Logger import error_log
from rsa.transform import int2bytes, bytes2int
from datetime import datetime
from Service.Models import *
from Service.Schema import *
from Service.Methods import send_mail
import psycopg2
import random
import yadisk
import bcrypt
import rsa
import os


app = FastAPI(openapi_tags=tags_metadata, docs_url="/", redoc_url=None)
app.include_router(API.router)
app.include_router(Services.router)
app.include_router(Files.router)
recovery_codes = []


@app.post("/login", tags=["Auth"])
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


@app.post("/register", tags=["Auth"])
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


@app.delete("/user/remove", tags=["Auth"])
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


@app.post("/recovery/send", tags=["Auth"])
async def recovery_send(login: str):
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


@app.post("/recovery/validate", tags=["Auth"])
async def recovery_validate(data: ResetPassword):
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


@app.get("/user/get_random", tags=["Users"])  # переписать запрос
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


@app.get("/user/find", tags=["Users"])
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


@app.get("/user/get_id", tags=["Users"])
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


@app.get("/user/get_nickname", tags=["Users"])
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


@app.get("/user/get_pubkey", tags=["Users"])
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


@app.get("/user/get_groups", tags=["Users"])
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


@app.put("/user/update_pubkey", tags=["Users"])
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


@app.put("/user/update_password", tags=["Users"])
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


@app.post("/chat/create", tags=["Users"])
async def create_chat(chat: Group, owner=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema NOT IN ("
                       "'information_schema', 'pg_catalog') AND table_schema IN('public', 'myschema');")
        if ('{0}'.format(chat.name),) in cursor.fetchall():
            return None
        cursor.execute("SELECT COUNT(*) FROM chats")
        res = cursor.fetchall()[0]
        res = str(res).split(',', 1)[0]
        max_id = int(str(res)[1:]) + 1
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


@app.get("/chat/get_id", tags=["Chats"])
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


@app.get("/chat/get_name", tags=["Chats"])
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


@app.get("/chat/get_users", tags=["Chats"])
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


@app.post("/chat/invite", tags=["Chats"])
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


@app.post("/chat/kick", tags=["Chats"])
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


@app.post("/message/send", tags=["Messages"])
async def send_message(message: Message, login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT login FROM users WHERE id={message.destination}")
        if cursor.fetchone()[0].lower() == "deleted":
            return JSONResponse(status_code=500)
        date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
        cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
        sender = cursor.fetchone()[0]
        msg = int2bytes(message.message)
        msg1 = int2bytes(message.message1)
        cursor.execute(f"INSERT INTO messages(date, from_id, to_id, message, message1, read) VALUES (to_timestamp("
                       f"'{date}','dd-mm-yy hh24:mi:ss'),'{sender}','{message.destination}',"
                       f"{psycopg2.Binary(msg)},{psycopg2.Binary(msg1)}, 0)")
        connect.commit()
        return JSONResponse(status_code=200)
    except Exception as e:
        error_log(e)
        return JSONResponse(status_code=500)
    finally:
        cursor.close()
        connect.close()


@app.post("/message/send/chat", tags=["Messages"])
async def send_chat_message(message: Message, login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT login FROM users WHERE id={message.destination}")
        if cursor.fetchone()[0].lower() == "deleted":
            return JSONResponse(status_code=500)
        date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
        cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
        sender_id = cursor.fetchone()[0]
        sender = f"{message.sender}_{sender_id}"
        msg = psycopg2.Binary(int2bytes(message.message))
        cursor.execute(f"INSERT INTO messages(date, from_id, to_id, message, message1, read) VALUES (to_timestamp("
                       f"'{date}', 'dd-mm-yy hh24:mi:ss'),'{sender}','{message.destination}',{msg},"
                       f"{msg}, 0)")
        connect.commit()
        return JSONResponse(status_code=200)
    except Exception as e:
        error_log(e)
        return JSONResponse(status_code=500)
    finally:
        cursor.close()
        connect.close()


@app.get("/message/get", tags=["Messages"])
async def get_message(chat_id: str, is_chat: int, max_id=None,
                      login=Depends(auth_handler.decode)):
    json_dict = {}
    connect, cursor = db_connect()
    cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
    user_id = cursor.fetchone()[0]
    if max_id is not None:
        max_id = f"AND id>{max_id} "
    else:
        max_id = ""
    if is_chat == 0:
        cursor.execute(f"SELECT * FROM messages WHERE to_id='{user_id}' AND from_id='{chat_id}' AND NOT from_id LIKE "
                       f"'g%' {max_id}ORDER BY ID")
        res = cursor.fetchall()
        if int(user_id) != int(chat_id):
            cursor.execute(f"SELECT * FROM messages WHERE to_id='{chat_id}' AND from_id='{user_id}' AND NOT from_id "
                           f"LIKE 'g%' {max_id}ORDER BY ID")
            res += cursor.fetchall()
        cursor.execute(f"UPDATE messages SET read=1 WHERE to_id='{user_id}' AND from_id LIKE '{chat_id}' AND read=0")
        res.sort()
        json_dict.update({"count": len(res)})
        try:
            json_dict.update({"max_id": res[len(res) - 1][0]})
        except IndexError:
            json_dict.update({"max_id": 0})
        for i in range(len(res)):
            cursor.execute(f"SELECT login FROM users WHERE id={res[i][2]}")
            json_dict.update({f"item_{i}": {"date": res[i][1], "from_id": cursor.fetchone()[0], "to_id": res[i][3],
                                            "message": bytes2int(res[i][4]), "message1": bytes2int(res[i][5]),
                                            "read": res[i][6]}})
    else:
        cursor.execute(f"SELECT * FROM messages WHERE to_id='{user_id}' AND from_id LIKE '{chat_id}%' {max_id}"
                       f"ORDER BY ID")
        res = cursor.fetchall()
        cursor.execute(f"UPDATE messages SET read=1 WHERE to_id='{user_id}' AND from_id LIKE '{chat_id}%' AND read=0")
        res.sort()
        json_dict.update({"count": len(res)})
        try:
            json_dict.update({"max_id": res[len(res) - 1][0]})
        except IndexError:
            json_dict.update({"max_id": 0})
        for i in range(len(res)):
            cursor.execute(f"SELECT login FROM users WHERE id={res[i][2].split('_', 1)[1]}")
            json_dict.update({f"item_{i}": {"date": res[i][1], "from_id": cursor.fetchone()[0], "to_id": res[i][3],
                                            "message": bytes2int(res[i][4]), "message1": bytes2int(res[i][5]),
                                            "read": res[i][6]}})
    connect.commit()
    cursor.close()
    connect.close()
    return json_dict


@app.get("/message/loop", tags=["Messages"])
async def get_loop_messages(login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"")
        cursor.execute(f"SELECT from_id FROM messages WHERE to_id='(SELECT id FROM users WHERE login='{login}')' "
                       f"AND read=0")
        new_msgs = []
        temp = ''
        for i in cursor.fetchall():
            if i[0] not in new_msgs:
                new_msgs.append(i[0])
        for i in new_msgs:
            temp += i + ', '
        return temp[:-2] if temp != '' else None
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()
