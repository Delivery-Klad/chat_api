try:  # для локального запуска
    from set_var import test
    test()
except ModuleNotFoundError:
    pass

import os
from datetime import datetime

from fastapi import FastAPI

from Service.Schema import *
from database.Connect import db_connect
from Service.Methods import parse_database_url
from Routers import Services, Files, Chats, Users, Messages, Recovery, Authorization, Alerts

app = FastAPI(openapi_tags=tags_metadata, docs_url="/", redoc_url=None)
app.include_router(Services.router)
app.include_router(Alerts.router)
app.include_router(Authorization.router)
app.include_router(Recovery.router)
app.include_router(Users.router)
app.include_router(Chats.router)
app.include_router(Messages.router)
app.include_router(Files.router)


@app.on_event("startup")
def startup_event():
    parse_database_url()
    connect, cursor = db_connect()
    cursor.execute(f"SELECT id FROM users WHERE login='Service'")
    try:
        cursor.fetchall()[0]
    except IndexError:
        date = datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')
        cursor.execute(f"INSERT INTO users(id, login, password, pubkey, email, last_activity) VALUES (0, 'Service',"
                       f"'fake_hash','service_pubkey','service_email', to_timestamp('{date}','dd-mm-yy hh24:mi:ss'))")
        connect.commit()
    cursor.close()
    connect.close()
