import datetime
from fastapi import APIRouter, Depends, Body, HTTPException
from typing import Annotated

from bleater.server.feed import get_feed, notify_thread
from bleater.models.posts import PostSubmitRequest, Post, Thread
from bleater.server.storage import BaseStorage, get_storage
from bleater.models.users import User, UserRegisterRequest, Notification

router = APIRouter(prefix="/api")


@router.get("/")
async def api_root():
    return {"message": "API"}


@router.post("/users/register")
async def user_register(
    body: UserRegisterRequest,
    storage: Annotated[BaseStorage, Depends(get_storage)],
) -> User | None:
    user = await storage.register_user(body.name)
    if user is None:
        raise HTTPException(400)
    return user


@router.get("/users/notifications")
async def user_notifications(
    user_id: str,
    storage: Annotated[BaseStorage, Depends(get_storage)],
) -> list[Notification]:
    notifications = await storage.get_user_notifications(user_id, 10)
    await storage.purge_user_notifications(user_id)
    return notifications


@router.post("/posts")
async def submit_post(
    body: PostSubmitRequest,
    storage: Annotated[BaseStorage, Depends(get_storage)],
) -> None:
    ts = int(datetime.datetime.now().timestamp())

    if body.parent_id is not None:
        # Check if the parent is not a reply itself
        parent = await storage.get_post(body.parent_id)
        if parent is None:
            raise HTTPException(400)
        if parent.parent_id is not None:
            body.parent_id = parent.parent_id

        # Notify relevant users
        await notify_thread(parent.id, ts, body.user_id, storage)

    await storage.submit_post(body, ts)


@router.get("/posts")
async def get_thread(
    post_id: str,
    storage: Annotated[BaseStorage, Depends(get_storage)],
) -> Thread:
    thread = await storage.get_thread(post_id)
    if thread is None:
        raise HTTPException(400)
    return thread


@router.get("/posts/recent")
async def recent_posts(
    storage: Annotated[BaseStorage, Depends(get_storage)],
) -> list[Post]:
    return await get_feed(storage)
