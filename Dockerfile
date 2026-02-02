FROM python:3.14-trixie

RUN pip install uv

RUN mkdir /app
WORKDIR /app

COPY . /app

ENV UV_NO_DEV=1

RUN uv sync --locked
CMD ["uv", "run", "main.py"]
