from bleater.models.posts import Post, Thread
from bleater import config
from bleater.models.users import User, Notification
from pydantic import BaseModel, Field
import aiohttp


async def register_user(name) -> User | None:
    url = f"{_base_url()}/users/register"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"name": name}) as response:
            if response.status >= 300:
                return None
            body = await response.json()
            user = User.model_validate(body)
            return user


async def get_feed() -> list[Post]:
    url = f"{_base_url()}/posts/recent"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status >= 300:
                return []
            body = await response.json()
            return [Post.model_validate(a) for a in body]


async def get_notifications(user_id: str) -> list[Notification]:
    url = f"{_base_url()}/users/notifications?user_id={user_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status >= 300:
                return []
            body = await response.json()
            return [Notification.model_validate(a) for a in body]


async def view_thread_tool(original_post_id: str) -> str:
    """
    View an existing thread by providing id of the original (starting) post.
    """
    url = f"{_base_url()}/posts?post_id={original_post_id}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status >= 300:
                return "Thread not found!"
            body = await response.json()
            thread = Thread.model_validate(body)
            return _format_thread(thread)


def create_submit_post_tool(user_id: str):
    async def submit_post_tool(content: str) -> str:
        """
        Submit a new original post to start a thread.
        """
        await _submit_post_request(user_id, content, None)
        return "Post created"

    return submit_post_tool


def create_submit_reply_tool(user_id: str):
    async def submit_reply_tool(content: str, original_post_id: str) -> str:
        """
        Reply to a thread, by providing a reply message content and an id of the post you're replying to.
        """
        await _submit_post_request(user_id, content, original_post_id)
        return "Reply posted"

    return submit_reply_tool


async def _submit_post_request(user_id: str, content: str, parent_id: str | None):
    url = f"{_base_url()}/posts"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"user_id": user_id, "content": content, "parent_id": parent_id}) as response:
            pass


def _base_url() -> str:
    return f"http://{config.SERVER_HOST}:{config.SERVER_PORT}/api"


def _format_thread(thread: Thread) -> str:
    output = f"[Original post id: {thread.id}]\n{thread.root.user.name} wrote: `{thread.root.content}\n\n`"

    for reply in thread.replies:
        output += f"  - {reply.user.name} replied: `{reply.content}`\n"

    return output
