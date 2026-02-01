from bleater.models.users import User
from pydantic import BaseModel


class PostSubmitRequest(BaseModel):
    """Post or response payload"""

    user_id: str
    content: str
    parent_id: str | None = None


class Post(BaseModel):
    id: str
    user: User
    content: str
    timestamp: int


class Thread(BaseModel):
    id: str
    root: Post
    replies: list[Post]
