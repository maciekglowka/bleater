from bleater.farm.tools import SubmitPost
from bleater.models.posts import PostSubmitRequest
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
    repository: Annotated[BaseStorage, Depends(get_storage)],
) -> User | None:
    user = await repository.register_user(body.name)
    if user is None:
        raise HTTPException(400)
    return user


@router.post("/posts")
async def user_register(
    body: PostSubmitRequest,
    repository: Annotated[BaseStorage, Depends(get_storage)],
) -> None:
    ts = int(datetime.datetime.now().timestamp())
    await repository.submit_post(body, ts)
