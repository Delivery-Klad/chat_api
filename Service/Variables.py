from Service.Auth import AuthHandler
import os

auth_handler = AuthHandler()
app_url = "chat-b4ckend.herokuapp.com"
admin_user = os.environ.get('key')
app_version = 3.6
old_version = 3.4
