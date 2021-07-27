from pydantic import BaseModel
from typing import Optional


class Auth(BaseModel):
    login: str
    password: str


class User(BaseModel):
    login: str
    password: str
    pubkey: str
    email: str


class Group(BaseModel):
    name: str


class Message(BaseModel):
    sender: Optional[str] = None
    destination: str
    message: int
    message1: Optional[int] = None


class Invite(BaseModel):
    name: str
    user: str


class NewPubkey(BaseModel):
    pubkey: str


class NewPassword(BaseModel):
    old_password: str
    new_password: str


class ResetPassword(BaseModel):
    code: str
    login: str
    password: Optional[str] = None
