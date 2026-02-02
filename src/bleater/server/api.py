from bleater.server.feed import get_feed
from bleater.models.posts import PostSubmitRequest, Post
from bleater.server.storage import BaseStorage, get_storage
from bleater.models.users import User, UserRegisterRequest
import datetime
from fastapi import APIRouter, Depends, Body, HTTPException
from typing import Annotated

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

    await storage.submit_post(body, ts)


@router.get("/posts/recent")
async def recent_posts(
    storage: Annotated[BaseStorage, Depends(get_storage)],
) -> list[Post]:
    return await get_feed(storage)
