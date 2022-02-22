import os
import linecache
from sys import exc_info

import rsa
import smtplib
import psycopg2
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from rsa.transform import bytes2int

import Service.Variables as Var


def db_connect():
    try:
        con = psycopg2.connect(host=Var.host,
                               database=Var.database,
                               user=Var.user,
                               port=Var.port,
                               password=Var.password)
        cur = con.cursor()
        return con, cur
    except Exception as e:
        error_log(e)
        return None


def create_tables():
    connect, cursor = db_connect()
    try:
        cursor.execute('CREATE TABLE IF NOT EXISTS users(id BIGSERIAL NOT NULL UNIQUE PRIMARY KEY,'
                       'login TEXT NOT NULL UNIQUE,'
                       'password TEXT NOT NULL,'
                       'pubkey TEXT NOT NULL,'
                       'email TEXT NOT NULL,'
                       'last_activity TIMESTAMP)')
        cursor.execute('CREATE TABLE IF NOT EXISTS chats(id TEXT NOT NULL UNIQUE,'
                       'name TEXT NOT NULL UNIQUE,'
                       'owner BIGINT NOT NULL REFERENCES users (id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS messages(id BIGSERIAL NOT NULL UNIQUE PRIMARY KEY,'
                       'date TIMESTAMP NOT NULL,'
                       'from_id TEXT NOT NULL,'
                       'to_id TEXT NOT NULL,'
                       'message BYTEA NOT NULL,'
                       'message1 BYTEA,'
                       'read INTEGER NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS members(group_id TEXT NOT NULL REFERENCES chats (id),'
                       'user_id BIGINT NOT NULL REFERENCES users (id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS links(id BIGSERIAL NOT NULL UNIQUE PRIMARY KEY,'
                       'longlink TEXT NOT NULL)')
        cursor.execute('CREATE TABLE IF NOT EXISTS alerts(id BIGINT NOT NULL UNIQUE PRIMARY KEY,'
                       'id_group TEXT NOT NULL)')
        connect.commit()
        return True
    finally:
        cursor.close()
        connect.close()


def parse_database_url():
    url = os.environ.get("DATABASE_URL")[11:].split('/')
    Var.database = url[1]
    url = url[0].split('@')
    Var.user, Var.password = url[0].split(':')
    Var.host, Var.port = url[1].split(':')
    create_tables()


def send_mail(email: str, title: str, text: str):
    try:
        password = os.environ.get('email_password')
        mail_login = os.environ.get('email_login')
        server = smtplib.SMTP_SSL("smtp.mail.ru", 465)
        msg = MIMEMultipart()
        msg['Subject'] = title
        msg['From'] = mail_login
        msg.attach(MIMEText(text, 'plain'))
        try:
            server.login(mail_login, password)
            server.sendmail(mail_login, email, msg.as_string())
            return True
        except Exception as e:
            error_log(e)
            return False
    except Exception as er:
        error_log(er)


def encrypt(msg: bytes, pubkey):
    try:
        pubkey = pubkey.split(', ')
        pubkey = rsa.PublicKey(int(pubkey[0]), int(pubkey[1]))
        encrypt_message = rsa.encrypt(msg, pubkey)
        return encrypt_message
    except Exception as e:
        error_log(e)
        return None


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
        cursor.execute(f"SELECT group_id FROM members WHERE user_id={user_id}")
        for i in cursor.fetchall():
            cursor.execute(f"SELECT name FROM chats WHERE id='{i[0]}'")
            groups.append(cursor.fetchone()[0])
        return groups
    except Exception as e:
        error_log(e)
        return None
    finally:
        cursor.close()
        connect.close()


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


def error_log(error):
    try:
        exc_type, exc_obj, tb = exc_info()
        _frame = tb.tb_frame
        linenos = tb.tb_lineno
        filename = _frame.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, linenos, _frame.f_globals)
        reason = f"EXCEPTION IN ({filename}, LINE {linenos} '{line.strip()}'): {exc_obj}"
        print(f"{reason}\n")
    except Exception as e:
        print(e)
        print("Возникла ошибка при обработке errorLog (Это вообще как?)")
