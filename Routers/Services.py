from Service.Variables import admin_user, auth_handler
from bs4 import BeautifulSoup as Soup
import requests
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/service", tags=["Service"])


@router.get("/")
async def api_awake():
    soup = Soup(requests.get("https://github.com/Delivery-Klad/chat_desktop/releases").text, 'html.parser')
    version_search = soup.find_all("span", {"class": "ml-1 wb-break-all"})
    old_ver_search = soup.find_all("div", {"class": "markdown-body"})

    old_version = float(version_search[len(version_search) - len(old_ver_search)].string)
    return f"{float(version_search[0].string)} {old_version}"


@router.patch("/")
async def generate_new_hex_secret(hex_length: int, login=Depends(auth_handler.decode)):
    if login == admin_user:
        import secrets
        return secrets.token_hex(hex_length)
    return None
