from fastapi.responses import HTMLResponse
from bleater.server.feed import get_feed
from bleater.server.storage import BaseStorage, get_storage
from dataclasses import dataclass
import datetime
from jinja2 import Environment, FileSystemLoader
import os
from typing import Callable, Annotated
from fastapi import APIRouter, Depends, Body, HTTPException


DIR = os.path.dirname(__file__)
TEMPLATE_PATH = os.path.join(DIR, "templates")
JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATE_PATH))

router = APIRouter()


@router.get("/")
async def feed(
    storage: Annotated[BaseStorage, Depends(get_storage)],
) -> HTMLResponse:
    feed = await get_feed(storage)
    template = JINJA_ENV.get_template("feed.jinja")
    return HTMLResponse(content=template.render(feed=feed), status_code=200)


@router.get("/posts")
async def feed(
    id: str,
    storage: Annotated[BaseStorage, Depends(get_storage)],
) -> HTMLResponse:
    thread = await storage.get_thread(id)
    template = JINJA_ENV.get_template("thread.jinja")
    return HTMLResponse(content=template.render(thread=thread), status_code=200)


def ts_format(value):
    dt = datetime.datetime.fromtimestamp(value)
    return dt.strftime("%d-%m-%y %H:%M")


JINJA_ENV.filters["ts_format"] = ts_format
