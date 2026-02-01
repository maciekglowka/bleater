from dataclasses import dataclass
from ollama import Client
from pydantic import BaseModel
from typing import TypeVar, Any, Callable

T = TypeVar("T", bound=BaseModel)


@dataclass
class ModelMessage:
    role: str
    content: str | dict[str, Any]


class ModelAdapter:
    def ask_structured(self, messages: list[ModelMessage], output: type[T]) -> T:
        raise NotImplementedError


class OllamaAdapter(ModelAdapter):
    def __init__(
        self, client: Client, model: str, options: dict[str, Any] | None = None
    ):
        self.client = client
        self.model = model
        self.options = options or {}

    def ask_structured(self, messages: list[ModelMessage], output: type[T]) -> T:
        print("@@@@")
        print(messages)
        ollama_messages = self._process_messages(messages)

        response = self.client.chat(
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
