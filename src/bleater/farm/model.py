from bleater import config
from dataclasses import dataclass
from ollama import AsyncClient
from pydantic import BaseModel
from typing import TypeVar, Any, Callable

T = TypeVar("T", bound=BaseModel)


@dataclass
class ModelMessage:
    role: str
    content: str | dict[str, Any]
    tool_name: str | None = None


@dataclass
class ModelToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class ModelResponse:
    content: str | None
    tool_calls: list[ModelToolCall]


class ModelAdapter:
    async def ask(self, messages: list[ModelMessage], tools: list[Callable] | None = None) -> ModelResponse:
        raise NotImplementedError

    async def ask_structured(self, messages: list[ModelMessage], output: type[T]) -> T:
        raise NotImplementedError


class OllamaAdapter(ModelAdapter):
    def __init__(
        self, *, client: AsyncClient | None = None, model: str | None = None, options: dict[str, Any] | None = None
    ):
        if client is None:
            self.client = AsyncClient(host=config.OLLAMA_HOST)
        else:
            self.client = client

        if model is None:
            self.model = config.OLLAMA_MODEL
        else:
            self.model = model

        self.options = {"num_ctx": config.OLLAMA_NUM_CTX}
        if options is not None:
            self.options | options

    async def ask(self, messages: list[ModelMessage], tools: list[Callable] | None = None) -> ModelResponse:
        print("@@@@")
        print(messages)
        ollama_messages = self._process_messages(messages)

        response = await self.client.chat(self.model, messages=ollama_messages, options=self.options, tools=tools)
        print("####")
        print(response)
        return ModelResponse(
            content=response.message.content,
            tool_calls=[
                ModelToolCall(name=a.function.name, arguments=dict(a.function.arguments))
                for a in (response.message.tool_calls or [])
            ],
        )

    async def ask_structured(self, messages: list[ModelMessage], output: type[T]) -> T:
        # print("@@@@")
        # print(messages)
        ollama_messages = self._process_messages(messages)

        response = await self.client.chat(
            self.model,
            messages=ollama_messages,
            options=self.options,
            format=output.model_json_schema(),
        )
        print("####")
        print(response)
        return output.model_validate_json(response.message.content)

    def _process_messages(self, messages: list[ModelMessage]) -> list[dict[str, Any]]:
        return [
            {
                "role": a.role,
                "content": a.content,
            }
            for a in messages
        ]
