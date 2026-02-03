from bleater import config
from dataclasses import dataclass
import enum
from google import genai
from logging import getLogger
import ollama
from pydantic import BaseModel
from typing import TypeVar, Any, Callable, Tuple

T = TypeVar("T", bound=BaseModel)

logger = getLogger(__name__)


class Role(enum.Enum):
    System = enum.auto
    User = enum.auto
    Assistant = enum.auto
    Tool = enum.auto


@dataclass
class ModelMessage:
    role: Role
    content: str | dict[str, Any]
    tool_name: str | None = None
    tool_calls: list[ModelToolCall] | None = None


@dataclass
class ModelToolCall:
    name: str
    arguments: dict[str, Any]


@dataclass
class ModelResponse:
    content: str | None
    tool_calls: list[ModelToolCall]


class ModelAdapter:
    async def ask(
        self, messages: list[ModelMessage], tools: list[Callable] | None = None
    ) -> ModelResponse:
        raise NotImplementedError

    async def ask_structured(self, messages: list[ModelMessage], output: type[T]) -> T:
        raise NotImplementedError


class OllamaAdapter(ModelAdapter):
    def __init__(
        self,
        *,
        client: ollama.AsyncClient | None = None,
        model: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if client is None:
            self.client = ollama.AsyncClient(host=config.OLLAMA_HOST)
        else:
            self.client = client

        if model is None:
            if not config.OLLAMA_MODEL:
                raise ValueError("Please specify a valid model for Ollama")
            self.model = config.OLLAMA_MODEL
        else:
            self.model = model

        self.options = {"num_ctx": config.OLLAMA_NUM_CTX}
        if options is not None:
            self.options | options

    async def ask(
        self, messages: list[ModelMessage], tools: list[Callable] | None = None
    ) -> ModelResponse:
        ollama_messages = self._process_messages(messages)

        response = await self.client.chat(
            self.model, messages=ollama_messages, options=self.options, tools=tools
        )
        logger.info(f"Model response: {response}")
        return ModelResponse(
            content=response.message.content,
            tool_calls=[
                ModelToolCall(
                    name=a.function.name, arguments=dict(a.function.arguments)
                )
                for a in (response.message.tool_calls or [])
            ],
        )

    async def ask_structured(self, messages: list[ModelMessage], output: type[T]) -> T:
        ollama_messages = self._process_messages(messages)

        response = await self.client.chat(
            self.model,
            messages=ollama_messages,
            options=self.options,
            format=output.model_json_schema(),
        )
        logger.info(f"Model response: {response}")
        return output.model_validate_json(response.message.content)

    def _process_messages(self, messages: list[ModelMessage]) -> list[dict[str, Any]]:
        return [
            {
                "role": self._parse_role(a.role),
                "content": a.content,
                **(
                    {}
                    if a.tool_calls is None
                    else {
                        "tool_calls": [
                            {"function": {"name": t.name, "arguments": t.arguments}}
                            for t in a.tool_calls
                        ]
                    }
                ),
                **({} if a.tool_name is None else {"tool_name": a.tool_name}),
            }
            for a in messages
        ]

    def _parse_role(self, role: Role) -> str:
        match role:
            case Role.System:
                return "system"
            case Role.User:
                return "user"
            case Role.Assistant:
                return "assistant"
            case Role.Tool:
                return "tool"
        raise ValueError


class GeminiAdapter(ModelAdapter):
    def __init__(
        self,
        *,
        client: genai.Client | None = None,
        model: str | None = None,
    ):
        if client is None:
            self.client = genai.Client(api_key=config.GEMINI_API_KEY).aio
        else:
            self.client = client

        if model is None:
            if not config.GEMINI_MODEL:
                raise ValueError("Please specify a valid model for Gemini")
            self.model = config.GEMINI_MODEL
        else:
            self.model = model

    async def ask(
        self, messages: list[ModelMessage], tools: list[Callable] | None = None
    ) -> ModelResponse:
        (system_prompt, gemini_messages) = self._process_messages(messages)

        response = await self.client.models.generate_content(
            model=self.model,
            contents=gemini_messages,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt, tools=tools
            ),
        )

        logger.info(f"Model response: {response}")
        return ModelResponse(
            content=response.text,
            tool_calls=[
                ModelToolCall(
                    name=a.function.name, arguments=dict(a.function.arguments)
                )
                for a in (response.message.tool_calls or [])
            ],
        )

    async def ask_structured(self, messages: list[ModelMessage], output: type[T]) -> T:
        (system_prompt, gemini_messages) = self._process_messages(messages)

        response = await self.client.models.generate_content(
            model=self.model,
            contents=gemini_messages,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=output,
            ),
        )

        logger.info(f"Model response: {response}")
        return output.model_validate_json(response.text)

    def _process_messages(self, messages: list[ModelMessage]) -> Tuple[str, list]:
        system_prompt = ""
        contents = []

        for message in messages:
            if message.role == Role.System:
                system_prompt += str(message.content)
                system_prompt += "\n"
                continue

            match message.role:
                case Role.User:
                    contents.append(
                        genai.types.UserContent(
                            parts=[
                                genai.types.Part.from_text(text=str(message.content))
                            ]
                        )
                    )
                case Role.Assistant:
                    parts = [genai.types.Part.from_text(text=str(message.content))]
                    if message.tool_calls:
                        parts += [
                            genai.types.Part.from_function_call(
                                name=t.name, args=t.arguments
                            )
                            for t in message.tool_calls
                        ]
                    contents.append(genai.types.ModelContent(parts=parts))
                case Role.Tool:
                    contents.append(
                        genai.types.ModelContent(
                            parts=[
                                genai.types.Part.from_function_response(
                                    # TODO specify error?
                                    name=message.tool_name,
                                    response={"output": message.content},
                                )
                            ]
                        )
                    )

        return (system_prompt, contents)
