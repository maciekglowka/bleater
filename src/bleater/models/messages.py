from bleater.models.users import User
from pydantic import BaseModel


class MessagePost(BaseModel):
    """Post message request"""

    user_id: str
    content: str
    parent_id: str | None = None


class Message(BaseModel):
    id: str
    user: User
    content: str
    timestamp: int


class Thread(BaseModel):
    id: str
    root: Message
    replies: list[Message]
