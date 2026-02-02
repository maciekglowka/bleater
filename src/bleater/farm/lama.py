from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader
import os
from typing import Callable

from .model import ModelAdapter, ModelMessage
from .tools import (
    register_user,
    get_feed,
    view_thread_tool,
    create_submit_post_tool,
    create_submit_reply_tool,
    get_notifications,
)

# TODO make a customizable template folder
DIR = os.path.dirname(__file__)
TEMPLATE_PATH = os.path.join(DIR, "templates")
JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATE_PATH))


@dataclass
class Tool:
    f: Callable


class Lama:
    def __init__(
        self,
        name: str,
        persona: str,
        *,
        actions_per_session: int = 5,
        user_id: str | None = None,
        system_prompt_template: str = "system_prompt.jinja",
        user_prompt_template: str = "user_prompt.jinja",
    ):
        self.history: list[ModelMessage] = []
        self.name = name
        self.persona = persona
        self.actions_per_session = actions_per_session
        self.user_id = user_id
        self.system_prompt_template = system_prompt_template
        self.user_prompt_template = user_prompt_template
        self.tools: dict[str, Tool] = {}

    async def build(self):
        if self.user_id is None:
            user = await register_user(self.name)
            if user is None:
                # TODO handle error
                return

        self.user_id = user.id

        # Register tools bound with user id
        self._register_tool(view_thread_tool)
        self._register_tool(create_submit_post_tool(self.user_id))
        self._register_tool(create_submit_reply_tool(self.user_id))

    async def run(self, model: ModelAdapter):
        action_no = 0

        await self._session_start()

        while True:
            action_no += 1

            await self._take_action(model)

            if action_no >= self.actions_per_session:
                return

    async def _session_start(self):
        print("-------------- ", self.name)
        feed = await get_feed()
        notifications = await get_notifications(self.user_id)

        system_template = JINJA_ENV.get_template(self.system_prompt_template)
        system_prompt = system_template.render(
            name=self.name, persona=self.persona, feed=feed, notifications=notifications
        )

        self.history = [
            ModelMessage(role="system", content=system_prompt),
        ]

    async def _take_action(self, model: ModelAdapter):
        user_template = JINJA_ENV.get_template(self.user_prompt_template)
        user_prompt = user_template.render(persona=self.persona)

        self.history.append(ModelMessage(role="user", content=user_prompt))

        response = await model.ask(self.history, self._tool_callables())

        self.history.append(ModelMessage(role="assistant", content=response.content))

        for tool in response.tool_calls:
            self.history.append(
                ModelMessage(role="assistant", content=f"Called: {tool.name} with arguments: {tool.arguments}")
            )
            try:
                result = await self.tools[tool.name].f(**tool.arguments)
                self.history.append(ModelMessage(role="tool", content=result, tool_name=tool.name))
            except Exception as e:
                self.history.append(ModelMessage(role="tool", content=str(e), tool_name=tool.name))

    def _register_tool(self, f: Callable):
        name = f.__name__

        self.tools[name] = Tool(f)

    def _tool_callables(self) -> list[Callable]:
        return [a.f for a in self.tools.values()]
