from bleater.models.posts import Post, Thread
from bleater import config
from bleater.models.users import User
from pydantic import BaseModel, Field
import aiohttp


class SubmitPost(BaseModel):
    """Submit a new original post to start a thread"""

    content: str = Field(..., max_length=140)


class SubmitReply(BaseModel):
    """Submit reply to a original post"""

    original_post_id: str
    content: str = Field(..., max_length=140)


class ViewThread(BaseModel):
    """View thread content with replies"""

    original_post_id: str


class Action(BaseModel):
    action: SubmitPost | ViewThread | SubmitReply


async def execute_action(action: Action, user_id: str) -> str | None:
    match action.action:
        case SubmitPost():
            return await submit_post(user_id, action.action)
        case SubmitReply():
            return await submit_reply(user_id, action.action)
        case ViewThread():
            print("%" * 200)
            return await get_thread(action.action.original_post_id)


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


async def get_thread(post_id: str) -> str | None:
    url = f"{_base_url()}/posts?post_id={post_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status >= 300:
                return None
            print("@@@@@@", response)
            body = await response.json()
            print("$$$$$$$$$$", body)
            thread = Thread.model_validate(body)
            return _format_thread(thread)


async def submit_post(user_id: str, post: SubmitPost) -> None:
    await _submit_post_request(user_id, post.content, None)


async def submit_reply(user_id: str, post: SubmitReply) -> None:
    await _submit_post_request(user_id, post.content, post.original_post_id)


async def _submit_post_request(user_id: str, content: str, parent_id: str | None):
    url = f"{_base_url()}/posts"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"user_id": user_id, "content": content, "parent_id": parent_id}) as response:
            print("@@@@@@", response)


def _base_url() -> str:
    return f"http://{config.SERVER_HOST}:{config.SERVER_PORT}/api"


def _format_thread(thread: Thread) -> str:
    output = f"[Original post id: {thread.id}]\n{thread.root.user.name} wrote: `{thread.root.content}\n\n`"

    for reply in thread.replies:
        output += f"  - {reply.user.name} replied: `{reply.content}`\n"

    return output
