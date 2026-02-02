from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader
import os
from typing import Callable

from .model import ModelAdapter, ModelMessage
from .tools import (
    register_user,
    Action,
    execute_action,
    get_feed,
)

DIR = os.path.dirname(__file__)
TEMPLATE_PATH = os.path.join(DIR, "templates")
JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATE_PATH))


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

    async def build(self):
        if self.user_id is None:
            user = await register_user(self.name)
            if user is None:
                # TODO handle error
                return

        self.user_id = user.id

    async def run(self, model: ModelAdapter):
        action_no = 0

        await self._session_start()

        while await self._take_action(model):
            action_no += 1
            if action_no >= self.actions_per_session:
                return

    async def _session_start(self):
        feed = await get_feed()

        system_template = JINJA_ENV.get_template(self.system_prompt_template)
        system_prompt = system_template.render(name=self.name, persona=self.persona, feed=feed)

        self.history = [
            ModelMessage(role="system", content=system_prompt),
            # ModelMessage(role="user", content=context.user_prompt),
        ]

    async def _take_action(self, model: ModelAdapter):
        user_template = JINJA_ENV.get_template(self.user_prompt_template)
        user_prompt = user_template.render(persona=self.persona)
        self.history.append(ModelMessage(role="user", content=user_prompt))

        response = await model.ask_structured(self.history, Action)

        self.history.append(ModelMessage(role="assistant", content=response.model_dump_json()))
        action_result = await execute_action(response, self.user_id)

        if action_result is not None:
            self.history.append(ModelMessage(role="tool", content=action_result))
