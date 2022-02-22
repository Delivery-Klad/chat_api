from datetime import datetime

import psycopg2
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Depends
from rsa.transform import int2bytes, bytes2int

from Service.Variables import auth_handler
from Service.Methods import db_connect
from Service.Models import *

router = APIRouter(prefix="/messages", tags=["Message"])


@router.get("/")
async def get_message(chat_id: str, is_chat: int, max_id: int,
                      login=Depends(auth_handler.decode)):
    json_dict = {}
    connect, cursor = db_connect()
    cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
    user_id = cursor.fetchone()[0]
    if is_chat == 0:
        cursor.execute(f"SELECT * FROM messages WHERE to_id='{user_id}' AND from_id='{chat_id}' AND NOT from_id LIKE "
                       f"'g%' AND id>{max_id} ORDER BY ID")
        res = cursor.fetchall()
        if int(user_id) != int(chat_id):
            cursor.execute(f"SELECT * FROM messages WHERE to_id='{chat_id}' AND from_id='{user_id}' AND NOT from_id "
                           f"LIKE 'g%' AND id>{max_id} ORDER BY ID")
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
        cursor.execute(f"SELECT * FROM messages WHERE to_id='{user_id}' AND from_id LIKE '{chat_id}%' AND id>{max_id} "
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


@router.post("/")
async def send_message(message: Message, login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT login FROM users WHERE id={message.destination}")
        if "deleted" in cursor.fetchone()[0].lower():
            return JSONResponse(status_code=500)
        date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
        cursor.execute(f"SELECT id FROM users WHERE login='{login}'")
        if not message.is_chat:
            sender = cursor.fetchone()[0]
            msg = int2bytes(message.message)
            msg1 = int2bytes(message.message1)
            cursor.execute(f"INSERT INTO messages(date, from_id, to_id, message, message1, read) VALUES (to_timestamp("
                           f"'{date}','dd-mm-yy hh24:mi:ss'),'{sender}','{message.destination}',"
                           f"{psycopg2.Binary(msg)},{psycopg2.Binary(msg1)}, 0)")
            connect.commit()
            return JSONResponse(status_code=200)
        else:
            sender_id = cursor.fetchone()[0]
            sender = f"{message.sender}_{sender_id}"
            msg = psycopg2.Binary(int2bytes(message.message))
            cursor.execute(f"INSERT INTO messages(date, from_id, to_id, message, message1, read) VALUES (to_timestamp("
                           f"'{date}', 'dd-mm-yy hh24:mi:ss'),'{sender}','{message.destination}',{msg},"
                           f"{msg}, 0)")
            connect.commit()
            return JSONResponse(status_code=200)
    finally:
        cursor.close()
        connect.close()
