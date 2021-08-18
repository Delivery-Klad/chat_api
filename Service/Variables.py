from Service.Auth import AuthHandler
from bs4 import BeautifulSoup as Soup
import requests
import os

auth_handler = AuthHandler()
app_url = "chat-b4ckend.herokuapp.com"
admin_user = os.environ.get('key')
app_version = None
old_version = None


def find_app_versions():
    global app_version, old_version
    soup = Soup(requests.get("https://github.com/Delivery-Klad/chat_desktop/releases").text, 'html.parser')
    version_search = soup.find_all("span", {"class": "css-truncate-target"})
    old_ver_search = soup.find_all("span", {"class": "flex-shrink-0 mb-md-2 mr-2 mr-md-0 Label Label--prerelease"})

    app_version = int(version_search[0].string)
    old_version = int(version_search[len(version_search) - len(old_ver_search) * 2 + 1].string)
