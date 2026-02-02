from pydantic import BaseModel


class UserRegisterRequest(BaseModel):
    name: str


class User(BaseModel):
    id: str | None = None
    name: str


class Notification(BaseModel):
    id: str
    user_id: str
    content: str
    post_id: str
    timestamp: int
    mentioned_user: User
