from Service.Variables import admin_user, auth_handler
from bs4 import BeautifulSoup as Soup
import requests
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/service", tags=["Service"])


@router.get("/awake")
async def api_awake():
    soup = Soup(requests.get("https://github.com/Delivery-Klad/chat_desktop/releases").text, 'html.parser')
    version_search = soup.find_all("span", {"class": "css-truncate-target"})
    old_ver_search = soup.find_all("span", {"class": "flex-shrink-0 mb-md-2 mr-2 mr-md-0 Label Label--prerelease"})

    app_version = float(version_search[0].string)
    old_version = float(version_search[len(version_search) - len(old_ver_search) * 2 + 1].string)
    return f"{app_version} {old_version}"


@router.get("/gen/secret")
async def gen_hex(hex_length: int, login=Depends(auth_handler.decode)):
    if login == admin_user:
        import secrets
        new_secret = secrets.token_hex(hex_length)
        return new_secret
    return None
