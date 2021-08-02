from fastapi import FastAPI, Depends
from Routers import Database, Services, Files, Chats, Users, Messages, Recovery, Authorization
from database.database import engine, SessionLocal
import database.models as db_models
from Service.Schema import *
from dependencies import get_db


# db_models.DataBase.metadata.create_all(bind=engine)
app = FastAPI(openapi_tags=tags_metadata, docs_url="/", redoc_url=None)  # dependencies=[Depends(get_db)]
app.include_router(Services.router)
app.include_router(Database.router)
app.include_router(Authorization.router)
app.include_router(Recovery.router)
app.include_router(Users.router)
app.include_router(Chats.router)
app.include_router(Messages.router)
app.include_router(Files.router)
