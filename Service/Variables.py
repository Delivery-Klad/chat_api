from Service.Auth import AuthHandler
import os

auth_handler = AuthHandler()
app_url = "chat-b4ckend.herokuapp.com"
admin_user = os.environ.get('key')

host = None
database = None
user = None
port = None
password = None
