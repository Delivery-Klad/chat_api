import random
from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
import psycopg2
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from rsa.transform import int2bytes, bytes2int
from Models import *
from Auth import AuthHandler
from Schema import *

app = FastAPI(openapi_tags=tags_metadata)
auth_handler = AuthHandler()
recovery_codes = []
secret = "root"


def db_connect():
    con = psycopg2.connect(
        host="ec2-54-247-107-109.eu-west-1.compute.amazonaws.com",
        database="de81d5uf5eagcd",
        user="guoucmhwdhynrf",
        port="5432",
        password="7720bda9eb76c990aee593f9064fa653136e3a047f989f53856b37549549ebe6")
    cur = con.cursor()
    return con, cur


def error_log(error):  # просто затычка, будет дописано
    try:
        print(error)
    except Exception as e:
        print(e)
        print("Возникла ошибка при обработке errorLog (Это вообще как?)")


@app.head("/api/awake", tags=["API"])
def api_awake(request: Request):
    print("awake")
    print(request.client.host)
    return True


@app.post("/recovery/send", tags=["API"])
def recovery_send(login: str):
    connect, cursor = db_connect()
    try:
        user_id = get_id(login)
        cursor.execute(f"SELECT email FROM users WHERE id={user_id}")
        email = cursor.fetchall()[0][0]
        code = random.randint(100000, 999999)
        print(code)
        recovery_codes.append(f"{login}_{code}")
        password = "12345qweryQ"
        mail_login = "recovery.chat@mail.ru"
        url = "smtp.mail.ru"
        server = smtplib.SMTP_SSL(url, 465)
        title = "Recovery code"
        text = "Your code: {0}".format(code)
        msg = MIMEMultipart()
        msg['Subject'] = title
        msg['From'] = mail_login
        body = text
        msg.attach(MIMEText(body, 'plain'))
        try:
            server.login(mail_login, password)
            server.sendmail(mail_login, email, msg.as_string())
        except Exception as e:
            print(f'Error {e}')
            return False
        print(recovery_codes)
        return True
    except Exception as e:
        error_log(e)
        return None


@app.post("/recovery/validate", tags=["API"])
def recovery_validate(data: ResetPassword):
    for i in recovery_codes:
        try:
            res = i.split(data.login)
            res.pop(0)
            print(f"{data.code} {res[0][1:]}")
            if data.code == res[0][1:]:
                if data.password is not None:
                    connect, cursor = db_connect()
                    cursor.execute(f"UPDATE users SET password='{data.password}' WHERE email='{data.login}'")
                    connect.commit()
                    cursor.close()
                    connect.close()
                return True
        except Exception as e:
            print(e)
            return False
    return False


@app.get("/tables/create", tags=["API"])
def create_tables(key: str):
    connect, cursor = db_connect()
    try:
        if key == secret:
            cursor.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER,'
                           'login TEXT,'
                           'password TEXT,'
                           'pubkey TEXT,'
                           'email TEXT)')
            cursor.execute('CREATE TABLE IF NOT EXISTS chats(id TEXT,'
                           'name TEXT,'
                           'owner INTEGER)')
            cursor.execute('CREATE TABLE IF NOT EXISTS messages(date TIMESTAMP,'
                           'from_id TEXT,'
                           'to_id TEXT,'
                           'message BYTEA,'
                           'message1 BYTEA,'
                           'file TEXT,'
                           'read INTEGER)')
            cursor.execute('CREATE TABLE IF NOT EXISTS links(id INTEGER,'
                           'longlink TEXT)')
        connect.commit()
        cursor.close()
        connect.close()
        return True
    except Exception as e:
        error_log(e)


@app.get("/tables/check", tags=["API"])
def check_tables(key: str, table: str):
    connect, cursor = db_connect()
    try:
        if key == secret:
            cursor.execute(f"SELECT * FROM {table}")
            return cursor.fetchall()
        return False
    except Exception as e:
        error_log(e)


@app.delete("/tables/drop", tags=["API"])
def create_tables(key: str):
    connect, cursor = db_connect()
    try:
        if key == secret:
            cursor.execute("DROP TABLE messages")
            cursor.execute("DROP TABLE users")
            cursor.execute("DROP TABLE chats")
            connect.commit()
        cursor.close()
        connect.close()
        return True
    except Exception as e:
        error_log(e)


@app.post("/auth", tags=["Users"])
def auth(data: Auth):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT password FROM users WHERE login='{data.login}'")
        if bcrypt.checkpw(data.password.encode('utf-8'), cursor.fetchall()[0][0].encode('utf-8')):
            token = auth_handler.encode_token(data.login)
            return token
        else:
            return False
    except IndexError:
        return None
    except Exception as e:
        error_log(e)


@app.get("/user/can_use_login", tags=["Users"])
def can_use_login(login: str):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
    try:
        cursor.fetchall()[0][0]
    except IndexError:
        return True
    return False


@app.get("/user/get_id", tags=["Users"])
def get_id(login: str):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
    return cursor.fetchall()[0][0]


@app.get("/user/get_nickname", tags=["Users"])
def get_nickname(id: int):
    try:
        connect, cursor = db_connect()
        cursor.execute(f"SELECT login FROM users WHERE id={id}")
        return cursor.fetchall()[0][0]
    except IndexError:
        return None


@app.get("/user/get_pubkey", tags=["Users"])
def get_pubkey(id: str):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT pubkey FROM users WHERE id={id}")
    return cursor.fetchall()[0][0]


@app.get("/user/get_groups", tags=["Users"])
def get_groups(user_id: int):
    connect, cursor = db_connect()
    groups = []
    cursor.execute("SELECT name FROM chats")
    res = cursor.fetchall()
    for el in res:
        cursor.execute(f"SELECT COUNT(id) FROM {el[0]} WHERE id='{user_id}'")
        tmp = cursor.fetchall()[0][0]
        if tmp == 1:
            groups.append(el[0])
    return groups


@app.post("/user/create", tags=["Users"])
def create_user(user: User):
    try:
        connect, cursor = db_connect()
        cursor.execute("SELECT MAX(id) FROM users")
        max_id = cursor.fetchall()[0][0]
        if max_id is not None:
            max_id += 1
        else:
            max_id = 0
        cursor.execute(f"INSERT INTO users VALUES ({max_id},'{user.login}','{user.password}','{user.pubkey}',"
                       f"'{user.email}')")
        connect.commit()
        return True
    except Exception as e:
        error_log(e)
        return JSONResponse(status_code=500)


@app.put("/user/update_pubkey", tags=["Users"])
def create_user(pubkey: NewPubkey, login=Depends(auth_handler.auth_wrapper)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"UPDATE users SET pubkey='{pubkey.pubkey}' WHERE login={login}")
        connect.commit()
        cursor.close()
        connect.close()
        return True
    except Exception as e:
        error_log(e)
        return False


@app.put("/user/update_password", tags=["Users"])
def create_user(data: NewPassword, login=Depends(auth_handler.auth_wrapper)):
    connect, cursor = db_connect()
    try:
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
def create_chat(chat: Group):
    try:
        connect, cursor = db_connect()
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema NOT IN ("
                       "'information_schema', 'pg_catalog') AND table_schema IN('public', 'myschema');")
        res = cursor.fetchall()
        if ('{0}'.format(chat.name),) in res:
            cursor.close()
            connect.close()
            return None
        max_id = get_max_chat_id() + 1
        cursor.execute(f"INSERT INTO chats VALUES ('g{max_id}', '{chat.name}', {chat.owner})")
        cursor.execute(f"CREATE TABLE IF NOT EXISTS {chat.name}(id INTEGER)")
        connect.commit()
        cursor.execute(f"INSERT INTO {chat.name} VALUES({chat.owner})")
        connect.commit()
        cursor.close()
        connect.close()
        return True
    except Exception as e:
        error_log(e)
        return False


@app.get("/chat/get_id", tags=["Chats"])
def get_chat_id(name: str):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT id FROM chats WHERE name='{name}'")
    group_id = cursor.fetchall()[0][0]
    cursor.close()
    connect.close()
    return group_id


def get_max_chat_id():
    connect, cursor = db_connect()
    cursor.execute("SELECT COUNT(*) FROM chats")
    res = cursor.fetchall()[0]
    res = str(res).split(',', 1)[0]
    cursor.close()
    connect.close()
    return int(str(res)[1:])


@app.get("/chat/get_name", tags=["Chats"])
def get_chat_name(group_id: str):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT name FROM chats WHERE id='{group_id}'")
    name = cursor.fetchall()[0][0]
    cursor.close()
    connect.close()
    return name


@app.get("/chat/get_users", tags=["Chats"])
def get_chat_users(name: str):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT id FROM {name}")
    res = cursor.fetchall()
    cursor.close()
    connect.close()
    return res


@app.get("/chat/get_owner", tags=["Chats"])
def get_chat_owner(group_id: str):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT owner FROM chats WHERE id='{group_id}'")
    res = cursor.fetchall()[0][0]
    cursor.close()
    connect.close()
    return res


@app.post("/chat/invite", tags=["Chats"])  # пароль и логин
def chat_invite(invite: Invite):
    connect, cursor = db_connect()
    cursor.execute(f"INSERT INTO {invite.name} VALUES({invite.user})")
    connect.commit()
    cursor.close()
    connect.close()
    return JSONResponse(status_code=200)


@app.post("/chat/kick", tags=["Chats"])  # пароль и логин
def chat_kick(invite: Invite):
    connect, cursor = db_connect()
    cursor.execute(f"DELETE FROM {invite.name} WHERE id={invite.user}")
    connect.commit()
    cursor.close()
    connect.close()
    return JSONResponse(status_code=200)


@app.post("/message/send", tags=["Messages"])
def send_message(message: Message):  # пароль и логин (а надо ли?)
    try:
        connect, cursor = db_connect()
        msg = int2bytes(message.message)
        msg1 = int2bytes(message.message1)
        cursor.execute(f"INSERT INTO messages VALUES (to_timestamp('{message.date}', 'dd-mm-yy hh24:mi:ss'),"
                       f"'{message.sender}','{message.destination}', {psycopg2.Binary(msg)},"
                       f"{psycopg2.Binary(msg1)}, '-', 0)")
        connect.commit()
        cursor.close()
        connect.close()
        return JSONResponse(status_code=200)
    except Exception as e:
        error_log(e)
        return JSONResponse(status_code=500)


@app.post("/message/send/chat", tags=["Messages"])
def send_chat_message(message: Message):  # пароль и логин (а надо ли?)
    try:
        connect, cursor = db_connect()
        msg = psycopg2.Binary(int2bytes(message.message))
        cursor.execute(
            f"INSERT INTO messages VALUES (to_timestamp('{message.date}', 'yy-mm-dd hh24:mi:ss'), '{message.sender}',"
            f"'{message.destination}', {msg}, {msg}, '-', 0)")
        connect.commit()
        cursor.close()
        connect.close()
        return JSONResponse(status_code=200)
    except Exception as e:
        error_log(e)
        return JSONResponse(status_code=500)


@app.get("/message/get", tags=["Messages"])
def get_message(user_id: int, chat_id: int, is_chat: int):
    connect, cursor = db_connect()
    cursor.execute(f"SELECT * FROM messages WHERE to_id='{user_id}' AND from_id='{chat_id}' AND NOT from_id LIKE 'g%' "
                   "ORDER BY date")
    res = cursor.fetchall()
    if is_chat == 0:
        cursor.execute(f"SELECT * FROM messages WHERE to_id='{chat_id}' AND from_id='{user_id}' AND NOT from_id LIKE "
                       f"'g%' ORDER BY date")
        res += cursor.fetchall()
    cursor.execute(f"UPDATE messages SET read=1 WHERE to_id='{user_id}' AND from_id LIKE '{chat_id}' AND read=0")
    connect.commit()
    res.sort()
    json_dict = {}
    for i in range(len(res)):
        json_dict.update({f"item_{i}": {"date": res[i][0], "from_id": res[i][1], "to_id": res[i][2],
                                        "message": bytes2int(res[i][3]), "message1": bytes2int(res[i][4]),
                                        "file": res[i][5], "read": res[i][6]}})
    cursor.close()
    connect.close()
    return json_dict


@app.get("/message/loop", tags=["Messages"])
def get_loop_messages(user_id: int):
    connect, cursor = db_connect()
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


@app.post("/file/upload", tags=["Files"])
def upload_file():
    with open("files/filename.file", "wb") as file:
        file.write("ff".encode('utf-8'))


@app.get("/url/shorter", tags=["Files"])
def url_shorter(url: str):
    connect, cursor = db_connect()
    cursor.execute("SELECT count(id) FROM links")
    max_id = cursor.fetchall()[0][0]
    print(max_id)
    print(url)
    # cursor.execute(f"INSERT INTO links VALUES({max_id + 1}, {url})")
    connect.commit()
    cursor.close()
    connect.close()
    return f"doc_{max_id}"


@app.post("/document/send", tags=["Files"])
def send_document():
    pass


@app.get("/document/get", tags=["Files"])
def get_document():
    pass
