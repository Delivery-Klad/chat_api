from fastapi import FastAPI
from Routers import Database, Services, Files, Chats, Users, Messages, Recovery, Authorization
from Service.Schema import *


app = FastAPI(openapi_tags=tags_metadata, docs_url="/", redoc_url=None)
app.include_router(Services.router)
app.include_router(Database.router)
app.include_router(Authorization.router)
app.include_router(Recovery.router)
app.include_router(Users.router)
app.include_router(Chats.router)
app.include_router(Messages.router)
app.include_router(Files.router)
