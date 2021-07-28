from database.Variables import admin_user, auth_handler, app_version, old_version
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/service", tags=["Service"])


@router.get("/awake")
async def api_awake():
    return f"{app_version} {old_version}"


@router.get("/gen/secret")
async def gen_hex(hex_length: int, login=Depends(auth_handler.decode)):
    if login == admin_user:
        import secrets
        new_secret = secrets.token_hex(hex_length)
        return new_secret
    return None
