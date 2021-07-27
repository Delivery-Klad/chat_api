from Service.Auth import AuthHandler
import yadisk
import os

auth_handler = AuthHandler()
y = yadisk.YaDisk(token=os.environ.get('yandex_token'))
app_url = "chat-b4ckend.herokuapp.com"
admin_user = os.environ.get('key')
app_version = 2.8
old_version = 2.6
