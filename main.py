try:  # для локального запуска
    from set_var import test
    test()
except ModuleNotFoundError:
    pass

import os
import Service.Variables as Var
from fastapi import FastAPI
from datetime import datetime
from database.Connect import db_connect
from Routers import Database, Services, Files, Chats, Users, Messages, Recovery, Authorization, Alerts
from Service.Schema import *


# db_models.DataBase.metadata.create_all(bind=engine)
app = FastAPI(openapi_tags=tags_metadata, docs_url="/", redoc_url=None)  # dependencies=[Depends(get_db)]
app.include_router(Services.router)
app.include_router(Alerts.router)
app.include_router(Database.router)
app.include_router(Authorization.router)
app.include_router(Recovery.router)
app.include_router(Users.router)
app.include_router(Chats.router)
app.include_router(Messages.router)
app.include_router(Files.router)


@app.on_event("startup")
async def startup_event():
    link = os.environ.get("DATABASE_URL")[11:].split('/')
    Var.database = link[1]
    link = link[0].split('@')
    Var.user, Var.password = link[0].split(':')
    Var.host, Var.port = link[1].split(':')
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
