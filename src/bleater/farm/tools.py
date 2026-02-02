from bleater.models.posts import Post
from bleater import config
from bleater.models.users import User
from pydantic import BaseModel
import aiohttp


class StartThread(BaseModel):
    """Submit a new original post to start a thread"""

    content: str


class SubmitReply(BaseModel):
    """Submit a reply to an existing post"""

    original_post_id: str
    content: str


class Action(BaseModel):
    action: StartThread | SubmitReply


async def execute_action(action: Action, user_id: str) -> str | None:
    match action.action:
        case StartThread():
            return await submit_post(user_id, action.action)
        case SubmitReply():
            return await submit_reply(user_id, action.action)


async def register_user(name) -> User | None:
    url = f"{_base_url()}/users/register"
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


async def get_feed() -> list[Post]:
    url = f"{_base_url()}/posts/recent"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status >= 300:
                return []
            print("@@@@@@", response)
            body = await response.json()
            print("$$$$$$$$$$", body)
            return [Post.model_validate(a) for a in body]


async def submit_post(user_id: str, post: StartThread) -> None:
    """
    Make a new post
    """
    await _submit_post_request(user_id, post.content, None)


async def submit_reply(user_id: str, post: SubmitReply) -> None:
    """
    Submit a post reply
    """
    await _submit_post_request(user_id, post.content, post.original_post_id)


async def _submit_post_request(user_id: str, content: str, parent_id: str | None):
    url = f"{_base_url()}/posts"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"user_id": user_id, "content": content, "parent_id": parent_id}) as response:
            print("@@@@@@", response)


def _base_url() -> str:
    return f"http://{config.SERVER_HOST}:{config.SERVER_PORT}/api"
