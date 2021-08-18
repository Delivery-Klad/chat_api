try:  # для локального запуска
    from set_var import test
    test()
except ModuleNotFoundError:
    pass

from fastapi import FastAPI
from Routers import Database, Services, Files, Chats, Users, Messages, Recovery, Authorization
from Service.Schema import *
from Service.Variables import find_app_versions


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


@app.on_event("startup")
async def startup():
    find_app_versions()
