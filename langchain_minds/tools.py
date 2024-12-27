"""AIMind tool."""

from importlib.metadata import version
from packaging.version import parse
import secrets
from typing import Any, Dict, List, Optional, Text, Type

from langchain_core.callbacks import (
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.utils import convert_to_secret_str, get_from_dict_or_env
from pydantic import BaseModel, Field, SecretStr


class AIMindDataSource(BaseModel):
    """
    The configuration for data sources used by the AIMindTool.
    """
    name = Text = Field(description="Name of the data source")
    engine: Text = Field(description="Engine (type) of the data source")
    description: Text = Field(description="Description of the data contained in the data source")
    connection_data: Dict[Text, Any] = Field(description="Connection parameters to establish a connection to the data source")
    tables = Optional[List[Text]] = Field(default=[], description="List of tables from the data source to be accessible by the Mind")


class AIMindAPIWrapper(BaseModel):
    """
    The API wrapper for the Minds API.
    """
    name: Text = Field(default=None)
    minds_api_key: SecretStr = Field(default=None)
    datasources: List[AIMindDataSource] = Field(default=None)

    # Not set by the user, but used internally.
    openai_client: Any = Field(default=None, exclude=True)

    def __init__(self, **data: Any) -> None:
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

        # Validate that the `openai` package can be imported.
        try:
            import openai
        except ImportError as e:
            raise ImportError(
                "Could not import openai python package. "
                "Please install it with `pip install openai`.",
            ) from e

        # Set the client based on the version of the `openai` package.
        try:
            openai_version = parse(version("openai"))
            if openai_version.major >= 1:
                client_params = {
                    "api_key": self.minds_api_key.get_secret_value(),
                    # "base_url": self.minds_api_base,
                }
                if not self.openai_client:
                    self.openai_client = openai.OpenAI(**client_params).chat.completions
            else:
                # self.openai_api_base = self.minds_api_base
                self.openai_api_key = self.minds_api_key.get_secret_value()
                self.openai_client = openai.ChatCompletion
        except AttributeError as exc:
            raise ValueError(
                "`openai` has no `ChatCompletion` attribute, this is likely "
                "due to an old version of the openai package. Try upgrading it "
                "with `pip install --upgrade openai`.",
            ) from exc
        
        # Validate that the `minds-sdk` package can be imported.
        try:
            from minds.client import Client
            from minds.datasources import DatabaseConfig
        except ImportError as e:
            raise ImportError(
                "Could not import minds-sdk python package. "
                "Please install it with `pip install minds-sdk`.",
            ) from e

        # Create a Minds client.
        minds_client = Client(
            self.minds_api_key.get_secret_value(), self.minds_api_base
        )

        # Create DatabaseConfig objects for each data source.
        datasources = []
        for ds in self.datasources:
            datasources.append(
                DatabaseConfig(
                    name=ds.name,
                    engine=ds.engine,
                    description=ds.description,
                    connection_data=ds.connection_data,
                    tables=ds.tables,
                )
            )

        # Create the Mind if it does not exist and set the mind attribute.
        self.mind = minds_client.minds.create(
            name=self.name, model_name=self.model, datasources=datasources, replace=True
        )


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
    api_wrapper: Type[BaseModel] = AIMindAPIWrapper

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
