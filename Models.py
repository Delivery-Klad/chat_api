from fastapi import Depends
from pydantic import BaseModel
from typing import Optional
from Auth import AuthHandler


auth_handler = AuthHandler()


class User(BaseModel):
    login: str
    password: str
    pubkey: str
    email: str


class Group(BaseModel):
    name: str
    owner: str


class Message(BaseModel):
    date: str
    sender: str
    destination: str
    message: int
    message1: Optional[int] = None


class Invite(BaseModel):
    name: str
    user: str


class NewPubkey(BaseModel):
    login: str
    password: str
    pubkey: str
    user_id: str


class NewPassword(BaseModel):
    login: Depends(auth_handler.auth_wrapper())
    old_password: str
    new_password: str


class ResetPassword(BaseModel):
    code: str
    login: str
    password: Optional[str] = None
