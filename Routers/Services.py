from database.Connect import db_connect
from database.Variables import admin_user, app_version, old_version, auth_handler
from Service.Logger import error_log
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/Service", tags=["Service"])


@router.get("/gen/secret")
async def gen_hex(hex_length: int, login=Depends(auth_handler.decode)):
    if login == admin_user:
        import secrets
        new_secret = secrets.token_hex(hex_length)
        return new_secret
    return None
