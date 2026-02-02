FROM python:3.14-trixie

RUN pip install uv

RUN mkdir /app
WORKDIR /app

COPY . /app

ENV UV_NO_DEV=1
ENV SERVER_BIND_ADDR=0.0.0.0

RUN uv sync --locked
CMD ["uv", "run", "main.py"]
