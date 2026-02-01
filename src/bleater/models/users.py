from pydantic import BaseModel


class UserRegisterRequest(BaseModel):
    name: str


class User(BaseModel):
    id: str | None = None
    name: str
