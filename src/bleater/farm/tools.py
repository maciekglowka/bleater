from bleater.models.users import User
from pydantic import BaseModel
import aiohttp

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 9999


class SubmitPost(BaseModel):
    content: str


class SubmitReply(BaseModel):
    original_post_id: str
    content: str


class FinishSession(BaseModel):
    pass


class Action(BaseModel):
    kind: SubmitPost | SubmitReply | FinishSession


async def execute_action(action: Action, user_id: str):
    match action.kind:
        case SubmitPost():
            await submit_post(user_id, action.kind)
        case SubmitReply():
            await submit_reply(user_id, action.kind)


async def register_user(name) -> User | None:
    url = f"http://{SERVER_HOST}:{SERVER_PORT}/api/users/register"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"name": name}) as response:
            if response.status >= 300:
                return None
            print("@@@@@@", response)
            body = await response.json()
            print("$$$$$$$$$$", body)
            user = User.model_validate(body)
            print("########", user)
            return user


async def submit_post(user_id: str, post: SubmitPost):
    """
    Make a new post
    """
    await _submit_post_request(user_id, post.content, None)


async def submit_reply(user_id: str, post: SubmitReply):
    """
    Submit a post reply
    """
    await _submit_post_request(user_id, post.content, post.original_post_id)


async def _submit_post_request(user_id: str, content: str, parent_id: str | None):
    url = f"http://{SERVER_HOST}:{SERVER_PORT}/api/posts"
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json={"user_id": user_id, "content": content, "parent_id": parent_id}
        ) as response:
            print("@@@@@@", response)
