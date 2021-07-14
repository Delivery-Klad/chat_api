import os
import rsa
import random
import yadisk
from fastapi import FastAPI, Request, Depends, File, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
import psycopg2
import bcrypt
import smtplib
import threading
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from rsa.transform import int2bytes, bytes2int
from Models import *
from Auth import AuthHandler
from Schema import *

app = FastAPI(openapi_tags=tags_metadata)
y = yadisk.YaDisk(token=os.environ.get('yandex_token'))
auth_handler = AuthHandler()
ip_table = []
recovery_codes = []
secret = os.environ.get('key')


def db_connect():
    con = psycopg2.connect(
        host=os.environ.get('host'),
        database=os.environ.get('database'),
        user=os.environ.get('user'),
        port=os.environ.get('port'),
        password=os.environ.get('password'))
    cur = con.cursor()
    return con, cur


def error_log(error):  # просто затычка, будет дописано
    try:
        print(error)
    except Exception as e:
        print(e)
        print("Возникла ошибка при обработке errorLog (Это вообще как?)")


def send_mail(email: str, title: str, text: str):
    try:
        password = os.environ.get('email_password')
        mail_login = os.environ.get('email_login')
        url = "smtp.mail.ru"
        server = smtplib.SMTP_SSL(url, 465)
        msg = MIMEMultipart()
        msg['Subject'] = title
        msg['From'] = mail_login
        body = text
        msg.attach(MIMEText(body, 'plain'))
        try:
            server.login(mail_login, password)
            server.sendmail(mail_login, email, msg.as_string())
            return True
        except Exception as e:
            print(f'Error {e}')
            return False
    except Exception as er:
        error_log(er)


def check_ip(login: str, ip: str):
    global ip_table
    if f"{login}://:{ip}" not in ip_table:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT email FROM users WHERE login='{login}'")
        email = cursor.fetchall()[0][0]
        send_mail(email, "Unknown device", f"Обнаружен вход с ip {ip}")
        cursor.close()
        connect.close()


def ip_thread(login: str, ip: str):
    thread = threading.Thread(target=check_ip, args=(login, ip))
    thread.start()


@app.head("/api/awake", tags=["API"])
async def api_awake():
    print("awake")
    return True


@app.get("/tables/create", tags=["API"])
async def create_tables(key: str):
    connect, cursor = db_connect()
    try:
        if key == secret:
            cursor.execute('CREATE TABLE IF NOT EXISTS users(id BIGSERIAL NOT NULL UNIQUE PRIMARY KEY,'
                           'login TEXT NOT NULL UNIQUE,'
                           'password TEXT NOT NULL,'
                           'pubkey TEXT NOT NULL,'
                           'email TEXT NOT NULL,'
                           'last_activity TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS chats(id TEXT NOT NULL UNIQUE,'
                           'name TEXT NOT NULL UNIQUE,'
                           'owner BIGINT NOT NULL)')
            cursor.execute('CREATE TABLE IF NOT EXISTS messages(id BIGSERIAL NOT NULL UNIQUE PRIMARY KEY,'
                           'date TIMESTAMP NOT NULL,'
                           'from_id TEXT NOT NULL,'
                           'to_id TEXT NOT NULL,'
                           'message BYTEA NOT NULL,'
                           'message1 BYTEA,'
                           'read INTEGER NOT NULL)')
            cursor.execute('CREATE TABLE IF NOT EXISTS links(id BIGSERIAL NOT NULL UNIQUE PRIMARY KEY,'
                           'longlink TEXT NOT NULL)')
            connect.commit()
        cursor.close()
        connect.close()
        return True
    except Exception as e:
        error_log(e)


@app.get("/tables/check", tags=["API"])
async def check_tables(key: str, table: str):
    connect, cursor = db_connect()
    try:
        if table == "messages":
            json_dict = {}
            cursor.execute(f"SELECT * FROM {table}")
            res = cursor.fetchall()
            res.sort()
            json_dict.update({"count": len(res)})
            for i in range(len(res)):
                json_dict.update(
                    {f"item_{i}": {"id": res[i][0], "date": res[i][1], "from_id": res[i][2], "to_id": res[i][3],
                                   "message": bytes2int(res[i][4]), "message1": bytes2int(res[i][5]),
                                   "read": res[i][6]}})
            cursor.close()
            connect.close()
            return json_dict
        if key == secret:
            cursor.execute(f"SELECT * FROM {table}")
            return cursor.fetchall()
        return False
    except Exception as e:
        error_log(e)
    finally:
        print('final')


@app.delete("/tables/drop", tags=["API"])
async def drop_tables(key: str, table: str):
    connect, cursor = db_connect()
    try:
        if key == secret:
            cursor.execute(f"DROP TABLE {table}")
            connect.commit()
        cursor.close()
        connect.close()
        return True
    except Exception as e:
        error_log(e)


@app.get("/database", tags=["API"])
async def database(key: str, query: str):
    connect, cursor = db_connect()
    try:
        if key == secret:
            if "select" in query.lower():
                return "Too use select operations /tables/check"
            cursor.execute(query)
            connect.commit()
            try:
                return cursor.fetchall()
            except Exception as e:
                print(e)
                return True
        return False
    except Exception as e:
        error_log(e)


@app.post("/auth", tags=["Auth"])
async def auth(data: Auth, request: Request):
    global ip_table
    connect, cursor = db_connect()
    try:
        ip_data = f"{data.login}://:{request.client.host}"
        if ip_data not in ip_table:
            ip_table.append(ip_data)
        cursor.execute(f"SELECT password FROM users WHERE login='{data.login}'")
        if bcrypt.checkpw(data.password.encode('utf-8'), cursor.fetchall()[0][0].encode('utf-8')):
            date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
            cursor.execute(f"UPDATE users SET last_activity=to_timestamp('{date}','dd-mm-yy hh24:mi:ss') WHERE "
                           f"login='{data.login}'")
            connect.commit()
            token = auth_handler.encode_token(data.login)
            return token
        else:
            return False
    except IndexError:
        return None
    except Exception as e:
        error_log(e)
    finally:
        cursor.close()
        connect.close()


@app.post("/recovery/send", tags=["Auth"])
async def recovery_send(login: str):
    connect, cursor = db_connect()
    try:
        user_id = get_id(login)
        cursor.execute(f"SELECT email FROM users WHERE id={user_id}")
        email = cursor.fetchall()[0][0]
        code = random.randint(100000, 999999)
        recovery_codes.append(f"{login}_{code}")
        print(recovery_codes)
        return send_mail(email, "Recovery code", "Your code: {0}".format(code))
    except Exception as e:
        error_log(e)
        return None


@app.post("/recovery/validate", tags=["Auth"])
async def recovery_validate(data: ResetPassword):
    for i in recovery_codes:
        try:
            res = i.split(data.login)
            res.pop(0)
            print(f"{data.code} {res[0][1:]}")
            if data.code == res[0][1:]:
                if data.password is not None:
                    connect, cursor = db_connect()
                    cursor.execute(f"UPDATE users SET password='{data.password}' WHERE login='{data.login}'")
                    connect.commit()
                    cursor.close()
                    connect.close()
                return True
            return False
        except Exception as e:
            print(e)
            return False
    return False


@app.get("/user/get_random", tags=["Users"])  # переписать запрос
async def get_random():
    try:
        connect, cursor = db_connect()
        res_dict = {}
        cursor.execute(f"SELECT id, login, last_activity FROM users ORDER BY random() LIMIT 30")
        res = cursor.fetchall()
        res_dict.update({"count": len(res)})
        for i in range(len(res)):
            res_dict.update({f"user_{i}": {"id": res[i][0], "login": res[i][1], "last_activity": res[i][2]}})
        cursor.close()
        connect.close()
        return res_dict
    except Exception as e:
        error_log(e)


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
    finally:
        cursor.close()
        connect.close()


@app.get("/user/get_id", tags=["Users"])
async def get_id(login: str):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
        return cursor.fetchall()[0][0]
    except IndexError:
        return None
    except Exception as e:
        error_log(e)


@app.get("/user/get_nickname", tags=["Users"])
async def get_nickname(id: int):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT login FROM users WHERE id={id}")
        return cursor.fetchall()[0][0]
    except IndexError:
        return None
    except Exception as e:
        error_log(e)


@app.get("/user/get_pubkey", tags=["Users"])
async def get_pubkey(id: str):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT pubkey FROM users WHERE id={id}")
        return cursor.fetchall()[0][0]
    except IndexError:
        return None
    except Exception as e:
        error_log(e)


@app.get("/user/get_groups", tags=["Users"])
async def get_groups(user_id: int):
    try:
        connect, cursor = db_connect()
        groups = []
        cursor.execute("SELECT name FROM chats")
        res = cursor.fetchall()
        for el in res:
            cursor.execute(f"SELECT COUNT(id) FROM {el[0]} WHERE id={user_id}")
            tmp = cursor.fetchall()[0][0]
            if tmp == 1:
                groups.append(el[0])
        return groups
    except Exception as e:
        error_log(e)


@app.post("/user/create", tags=["Users"])
async def create_user(user: User):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT id FROM users WHERE login='{user.login}'")
        try:
            cursor.fetchall()[0][0]
        except IndexError:
            date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
            cursor.execute(
                f"INSERT INTO users(login, password, pubkey, email, last_activity) VALUES ('{user.login}','{user.password}',"
                f"'{user.pubkey}','{user.email}', to_timestamp('{date}','dd-mm-yy hh24:mi:ss'))")
            connect.commit()
            return True
        return False
    except Exception as e:
        error_log(e)
        return JSONResponse(status_code=500)


@app.put("/user/update_pubkey", tags=["Users"])
async def create_user(pubkey: NewPubkey, request: Request, login=Depends(auth_handler.auth_wrapper)):
    ip_thread(login, request.client.host)
    try:
        connect, cursor = db_connect()
        cursor.execute(f"UPDATE users SET pubkey='{pubkey.pubkey}' WHERE login='{login}'")
        connect.commit()
        cursor.close()
        connect.close()
        return True
    except Exception as e:
        error_log(e)
        return False


@app.put("/user/update_password", tags=["Users"])
async def create_user(data: NewPassword, request: Request, login=Depends(auth_handler.auth_wrapper)):
    ip_thread(login, request.client.host)
    try:
        connect, cursor = db_connect()
        try:
            cursor.execute(f"SELECT password FROM users WHERE login='{login}'")
            res = bcrypt.checkpw(data.old_password.encode('utf-8'), cursor.fetchall()[0][0].encode('utf-8'))
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


@app.post("/chat/create", tags=["Users"])
async def create_chat(chat: Group, request: Request, owner=Depends(auth_handler.auth_wrapper)):
    ip_thread(owner, request.client.host)
    try:
        connect, cursor = db_connect()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema NOT IN ("
                       "'information_schema', 'pg_catalog') AND table_schema IN('public', 'myschema');")
        res = cursor.fetchall()
        if ('{0}'.format(chat.name),) in res:
            cursor.close()
            connect.close()
            return None
        cursor.execute("SELECT COUNT(*) FROM chats")
        res = cursor.fetchall()[0]
        res = str(res).split(',', 1)[0]
        max_id = int(str(res)[1:]) + 1
        cursor.execute(f"SELECT id FROM users WHERE login='{owner}'")
        owner_id = cursor.fetchall()[0][0]
        cursor.execute(f"INSERT INTO chats VALUES ('g{max_id}', '{chat.name}', {owner_id})")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {chat.name}(id BIGINT REFERENCES users (id))")
        connect.commit()
        cursor.execute(f"INSERT INTO {chat.name} VALUES({owner_id})")
        connect.commit()
        cursor.close()
        connect.close()
        return True
    except Exception as e:
        error_log(e)
        return False


@app.get("/chat/get_id", tags=["Chats"])
async def get_chat_id(name: str):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT id FROM chats WHERE name='{name}'")
        group_id = cursor.fetchall()[0][0]
        cursor.close()
        connect.close()
        return group_id
    except Exception as e:
        error_log(e)


@app.get("/chat/get_name", tags=["Chats"])
async def get_chat_name(group_id: str):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT name FROM chats WHERE id='{group_id}'")
        name = cursor.fetchall()[0][0]
        cursor.close()
        connect.close()
        return name
    except Exception as e:
        error_log(e)


@app.get("/chat/get_users", tags=["Chats"])
async def get_chat_users(group_id: str):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT name FROM chats WHERE id='{group_id}'")
        name = cursor.fetchall()[0][0]
        cursor.execute(f"SELECT id FROM {name}")
        res = cursor.fetchall()
        cursor.close()
        connect.close()
        return res
    except Exception as e:
        error_log(e)


@app.post("/chat/invite", tags=["Chats"])
async def chat_invite(invite: Invite, request: Request, user=Depends(auth_handler.auth_wrapper)):
    ip_thread(user, request.client.host)
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT owner FROM chats WHERE name='{invite.name}'")
        cursor.execute(f"SELECT login FROM users WHERE id='{cursor.fetchall()[0][0]}'")
        owner = cursor.fetchall()[0][0]
        if owner == user:
            cursor.execute(f"INSERT INTO {invite.name} VALUES({invite.user})")
            connect.commit()
            cursor.close()
            connect.close()
            return True
        return False
    except Exception as e:
        error_log(e)


@app.post("/chat/kick", tags=["Chats"])
async def chat_kick(invite: Invite, request: Request, user=Depends(auth_handler.auth_wrapper)):
    ip_thread(user, request.client.host)
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT owner FROM chats WHERE name='{invite.name}'")
        cursor.execute(f"SELECT login FROM users WHERE id='{cursor.fetchall()[0][0]}'")
        owner = cursor.fetchall()[0][0]
        if owner == user:
            cursor.execute(f"DELETE FROM {invite.name} WHERE id={invite.user}")
            connect.commit()
            cursor.close()
            connect.close()
            return True
        return False
    except Exception as e:
        error_log(e)


@app.post("/message/send", tags=["Messages"])
async def send_message(message: Message, request: Request, login=Depends(auth_handler.auth_wrapper)):
    try:
        ip_thread(login, request.client.host)
        date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
        connect, cursor = db_connect()
        cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
        sender = cursor.fetchall()[0][0]
        msg = int2bytes(message.message)
        msg1 = int2bytes(message.message1)
        cursor.execute(f"INSERT INTO messages(date, from_id, to_id, message, message1, read) VALUES (to_timestamp("
                       f"'{date}','dd-mm-yy hh24:mi:ss'),'{sender}','{message.destination}',"
                       f"{psycopg2.Binary(msg)},{psycopg2.Binary(msg1)}, 0)")
        connect.commit()
        cursor.close()
        connect.close()
        return JSONResponse(status_code=200)
    except Exception as e:
        error_log(e)
        return JSONResponse(status_code=500)


@app.post("/message/send/chat", tags=["Messages"])
async def send_chat_message(message: Message, request: Request, login=Depends(auth_handler.auth_wrapper)):
    try:
        ip_thread(login, request.client.host)
        date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
        connect, cursor = db_connect()
        msg = psycopg2.Binary(int2bytes(message.message))
        cursor.execute(f"INSERT INTO messages(date, from_id, to_id, message, message1, read) VALUES (to_timestamp("
                       f"'{date}', 'dd-mm-yy hh24:mi:ss'),'{message.sender}','{message.destination}',{msg},"
                       f"{msg}, 0)")
        connect.commit()
        cursor.close()
        connect.close()
        return JSONResponse(status_code=200)
    except Exception as e:
        error_log(e)
        return JSONResponse(status_code=500)


@app.get("/message/get", tags=["Messages"])
async def get_message(chat_id: str, is_chat: int, request: Request, max_id=None, login=Depends(auth_handler.auth_wrapper)):
    ip_thread(login, request.client.host)
    json_dict = {}
    connect, cursor = db_connect()
    cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
    user_id = cursor.fetchall()[0][0]
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
            name = cursor.fetchall()[0][0]
            json_dict.update({f"item_{i}": {"date": res[i][1], "from_id": name, "to_id": res[i][3],
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
            name = cursor.fetchall()[0][0]
            json_dict.update({f"item_{i}": {"date": res[i][1], "from_id": name, "to_id": res[i][3],
                                            "message": bytes2int(res[i][4]), "message1": bytes2int(res[i][5]),
                                            "read": res[i][6]}})
    connect.commit()
    cursor.close()
    connect.close()
    return json_dict


@app.get("/message/loop", tags=["Messages"])
async def get_loop_messages(request: Request, login=Depends(auth_handler.auth_wrapper)):
    ip_thread(login, request.client.host)
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
        user_id = cursor.fetchall()[0][0]
        cursor.execute(f"SELECT from_id FROM messages WHERE to_id='{user_id}' AND read=0")
        res = cursor.fetchall()
        new_msgs = []
        temp = ''
        for i in res:
            if i[0] not in new_msgs:
                new_msgs.append(i[0])
        for i in new_msgs:
            temp += i + ', '
        if temp != '':
            return temp[:-2]
        else:
            return None
    except Exception as e:
        error_log(e)


@app.get("/file/get/file_{id}", tags=["Files"])
async def get_file(id):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT longlink FROM links WHERE id={id}")
        try:
            res = cursor.fetchall()[0][0]
        except IndexError:
            res = None
        cursor.close()
        connect.close()
        return RedirectResponse(url=res)
    except Exception as e:
        error_log(e)


@app.post("/file/upload", tags=["Files"])
async def upload_file(file: UploadFile = File(...)):
    try:
        with open(file.filename, "wb") as out_file:
            content = await file.read()
            out_file.write(content)
        print(os.stat(file.filename).st_size)
        try:
            y.upload(file.filename, '/' + file.filename)
        except Exception:
            pass
        link = y.get_download_link('/' + file.filename)
        os.remove(file.filename)
        connect, cursor = db_connect()
        cursor.execute("SELECT count(id) FROM links")
        max_id = int(cursor.fetchall()[0][0]) + 1
        cursor.execute(f"INSERT INTO links VALUES({max_id}, '{link}')")
        connect.commit()
        return max_id
    except Exception as e:
        error_log(e)


@app.get("/url/shorter", tags=["Files"])
async def url_shorter(url: str, destination: str, request: Request, login=Depends(auth_handler.auth_wrapper)):
    ip_thread(login, request.client.host)
    try:
        connect, cursor = db_connect()
        link = f"chat-b4ckend.herokuapp.com/file/get/file_{url}"
        date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
        cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
        user_id = cursor.fetchall()[0][0]
        cursor.execute(f"SELECT pubkey FROM users WHERE id={destination}")
        res = cursor.fetchall()[0][0]
        encrypt_link = encrypt(link.encode('utf-8'), res)
        cursor.execute(f"SELECT pubkey FROM users WHERE id={user_id}")
        res = cursor.fetchall()[0][0]
        encrypt_link1 = encrypt(link.encode('utf-8'), res)
        cursor.execute(f"INSERT INTO messages(date, from_id, to_id, message, message1, read) VALUES "
                       f"(to_timestamp('{date}','dd-mm-yy hh24:mi:ss'),'{user_id}','{destination}',"
                       f"{psycopg2.Binary(encrypt_link)},{psycopg2.Binary(encrypt_link1)}, 0)")
        connect.commit()
        cursor.close()
        connect.close()
        return True
    except Exception as e:
        error_log(e)


@app.get("/url/shorter/chat", tags=["Files"])
async def url_shorter_chat(url: str, sender: str, destination: str, request: Request,
                           login=Depends(auth_handler.auth_wrapper)):
    ip_thread(login, request.client.host)
    try:
        connect, cursor = db_connect()
        link = f"chat-b4ckend.herokuapp.com/file/get/file_{url}"
        date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
        cursor.execute(f"SELECT pubkey FROM users WHERE id={destination}")
        res = cursor.fetchall()[0][0]
        encrypt_link = encrypt(link.encode('utf-8'), res)
        cursor.execute(f"INSERT INTO messages(date, from_id, to_id, message, message1, read) VALUES "
                       f"(to_timestamp('{date}','dd-mm-yy hh24:mi:ss'),'{sender}','{destination}',"
                       f"{psycopg2.Binary(encrypt_link)},{psycopg2.Binary(encrypt_link)}, 0)")
        connect.commit()
        cursor.close()
        connect.close()
        return True
    except Exception as e:
        error_log(e)


def encrypt(msg: bytes, pubkey):
    try:
        pubkey = pubkey.split(', ')
        pubkey = rsa.PublicKey(int(pubkey[0]), int(pubkey[1]))
        encrypt_message = rsa.encrypt(msg, pubkey)
        return encrypt_message
    except Exception as e:
        print(e)
