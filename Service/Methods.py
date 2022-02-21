import os

import rsa
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from rsa.transform import bytes2int, int2bytes

from Service.Logger import error_log
from database.Connect import db_connect


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
