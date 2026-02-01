from pydantic import BaseModel


class UserRegister(BaseModel):
    name: str


class User(BaseModel):
    id: str | None = None
    name: str
