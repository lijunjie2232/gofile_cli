from pydantic import BaseModel


class Token(BaseModel):
    id: str
    token: str


class Account(BaseModel):
    id: str
    address: str
    quota: int
    used: int
    isDisabled: bool
    isDeleted: bool
    createdAt: str
    updatedAt: str
    token: Token
