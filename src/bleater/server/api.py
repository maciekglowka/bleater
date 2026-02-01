from bleater.models.messages import MessagePost
from bleater.server.storage import BaseStorage, get_storage
from bleater.models.users import User, UserRegister
import datetime
from fastapi import APIRouter, Depends, Body, HTTPException
from typing import Annotated

router = APIRouter(prefix="/api")


@router.get("/")
async def api_root():
    return {"message": "API"}


@router.post("/users/register")
async def user_register(
    body: UserRegister,
    repository: Annotated[BaseStorage, Depends(get_storage)],
) -> User | None:
    user = await repository.register_user(body.name)
    if user is None:
        raise HTTPException(400)
    return user


@router.post("/messages")
async def user_register(
    body: MessagePost,
    repository: Annotated[BaseStorage, Depends(get_storage)],
) -> None:
    ts = int(datetime.datetime.now().timestamp())
    await repository.post_message(body, ts)
