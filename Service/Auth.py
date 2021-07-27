from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import os


class AuthHandler:
    security = HTTPBearer()
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    secret = os.environ.get('secret')

    def encode(self, login):
        payload = {'exp': datetime.utcnow() + timedelta(days=0, minutes=10), 'iat': datetime.utcnow(), 'sub': login}
        return jwt.encode(payload, self.secret, algorithm='HS256')

    def decode(self, auth: HTTPAuthorizationCredentials = Security(security)):
        try:
            payload = jwt.decode(auth.credentials, self.secret, algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Expired signature')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail='Invalid token')
