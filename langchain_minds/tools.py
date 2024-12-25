"""AIMind tool."""

import secrets
from typing import Any, Optional, Text, Type

from langchain_core.callbacks import (
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.utils import convert_to_secret_str, get_from_dict_or_env
from pydantic import BaseModel, Field, SecretStr


class AIMindToolInput(BaseModel):
    """
    The input schema for the AIMindTool.
    """
    name: Text = Field(default=None, description="Name of the Minds")
    minds_api_key: SecretStr = Field(default=None, description="Minds API key")

    def __init__(self, **data: Any) -> None:
        """
        Runs validations on the input data provided to the AIMindTool.
        """
        super().__init__(**data)

        # Validate that the API key and base URL are available.
        self.minds_api_key = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "minds_api_key",
                "MINDS_API_KEY",
            )
        )

        # If a name is not provided, generate a random one.
        if not self.name:
            self.name = f"lc_mind_{secrets.token_hex(5)}"


class AIMindTool(BaseTool):  # type: ignore[override]
    """AIMind tool.

    Setup:
        # TODO: Replace with relevant packages, env vars.
        Install ``langchain-minds`` and set environment variable ``MINDS_API_KEY``.

        .. code-block:: bash

            pip install -U langchain-minds
            export MINDS_API_KEY="your-api-key"

    Instantiation:
        .. code-block:: python

            tool = AIMindTool(
                # TODO: init params
            )

    Invocation with args:
        .. code-block:: python

            # TODO: invoke args
            tool.invoke({...})

        .. code-block:: python

            # TODO: output of invocation

    Invocation with ToolCall:

        .. code-block:: python

            # TODO: invoke args
            tool.invoke({"args": {...}, "id": "1", "name": tool.name, "type": "tool_call"})

        .. code-block:: python

            # TODO: output of invocation
    """  # noqa: E501

    # TODO: Set tool name and description
    name: str = "TODO: Tool name"
    """The name that is passed to the model when performing tool calling."""
    description: str = "TODO: Tool description."
    """The description that is passed to the model when performing tool calling."""
    args_schema: Type[BaseModel] = AIMindToolInput
    """The schema that is passed to the model when performing tool calling."""

    # TODO: Add any other init params for the tool.
    # param1: Optional[str]
    # """param1 determines foobar"""

    def _run(
        self, query: Text, *, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        return query

    # TODO: Implement if tool has native async functionality, otherwise delete.

    # async def _arun(
    #     self,
    #     a: int,
    #     b: int,
    #     *,
    #     run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    # ) -> str:
    #     ...
