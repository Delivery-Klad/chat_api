import os
from datetime import datetime

import yadisk
import psycopg2
from fastapi import File, UploadFile
from fastapi.responses import RedirectResponse
from fastapi import APIRouter, Depends

from Service.Variables import auth_handler, app_url
from Service.Methods import encrypt, db_connect, error_log


router = APIRouter(prefix="/file", tags=["File"])
y = yadisk.YaDisk(token=os.environ.get('yandex_token'))


@router.get("/{id}")
async def get_file(id):
    connect, cursor = db_connect()
    try:
        cursor.execute(f"SELECT longlink FROM links WHERE id={id}")
        try:
            res = cursor.fetchone()[0]
        except IndexError:
            res = None
        return RedirectResponse(url=res)
    finally:
        cursor.close()
        connect.close()


@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    connect, cursor = db_connect()
    try:
        with open(file.filename, "wb") as out_file:
            content = await file.read()
            out_file.write(content)
        print(os.stat(file.filename).st_size)
        try:
            y.upload(file.filename, '/' + file.filename)
        except Exception as e:
            error_log(e)
        cursor.execute("SELECT count(id) FROM links")
        max_id = int(cursor.fetchone()[0]) + 1
        cursor.execute(f"INSERT INTO links VALUES({max_id}, '{y.get_download_link('/' + file.filename)}')")
        connect.commit()
        return max_id
    finally:
        os.remove(file.filename)
        cursor.close()
        connect.close()


@router.patch("/")
async def url_shorter(url: str, destination: str, login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        link = f"{app_url}/file/{url}".encode('utf-8')
        date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
        cursor.execute(f"SELECT id,pubkey FROM users WHERE login='{login}'")
        data = cursor.fetchone()
        encrypt_link1 = encrypt(link, data[1])
        cursor.execute(f"SELECT pubkey FROM users WHERE id={destination}")
        encrypt_link = encrypt(link, cursor.fetchone()[0])
        cursor.execute(f"INSERT INTO messages(date, from_id, to_id, message, message1, read) VALUES "
                       f"(to_timestamp('{date}','dd-mm-yy hh24:mi:ss'),'{data[0]}','{destination}',"
                       f"{psycopg2.Binary(encrypt_link)},{psycopg2.Binary(encrypt_link1)}, 0)")
        connect.commit()
        return True
    finally:
        cursor.close()
        connect.close()


@router.put("/")
async def url_shorter_chat(url: str, sender: str, target: str, login=Depends(auth_handler.decode)):
    connect, cursor = db_connect()
    try:
        date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
        cursor.execute(f"SELECT pubkey FROM users WHERE id={target}")
        encrypt_link = encrypt(f"{app_url}/file/get/file_{url}".encode('utf-8'), cursor.fetchone()[0])
        cursor.execute(f"INSERT INTO messages(date, from_id, to_id, message, message1, read) VALUES "
                       f"(to_timestamp('{date}','dd-mm-yy hh24:mi:ss'),'{sender}','{target}',"
                       f"{psycopg2.Binary(encrypt_link)},{psycopg2.Binary(encrypt_link)}, 0)")
        connect.commit()
        return True
    finally:
        cursor.close()
        connect.close()
