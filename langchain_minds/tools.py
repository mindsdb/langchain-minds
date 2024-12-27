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
    name: Text = Field(description="Name of the data source")
    engine: Text = Field(description="Engine (type) of the data source")
    description: Text = Field(description="Description of the data contained in the data source")
    connection_data: Dict[Text, Any] = Field(description="Connection parameters to establish a connection to the data source")
    tables: Optional[List[Text]] = Field(default=[], description="List of tables from the data source to be accessible by the Mind")


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
        """
        Initializes the API wrapper for the Minds API.
        Validates the API key is available and sets the name if not provided.
        Validates the required packages can be imported and creates the Mind.
        Initializes the OpenAI client used to interact with the created Mind.
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
                    "base_url": "https://mdb.ai/"
                }
                if not self.openai_client:
                    self.openai_client = openai.OpenAI(**client_params).chat.completions
            else:
                self.openai_api_base = "https://mdb.ai/"
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
            self.minds_api_key.get_secret_value(),
            # self.minds_api_base
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
        minds_client.minds.create(
            name=self.name, datasources=datasources, replace=True
        )

    def run(self, query: Text) -> Text:
        """
        Run the query against the Minds API and return the response.
        """
        completion = self.openai_client.create(
            model=self.name,
            messages=[{"role": "user", "content": query}],
            stream=False,
        )

        return completion.choices[0].message.content


class AIMindTool(BaseTool):  # type: ignore[override]
    """AIMind tool.

    Setup:
        Install ``langchain-minds`` and set environment variable ``MINDS_API_KEY``.

        .. code-block:: bash

            pip install -U langchain-minds
            export MINDS_API_KEY="your-api-key"

    Instantiation:
        .. code-block:: python
            from langchain_minds import AIMindDataSource, AIMindAPIWrapper, AIMindTool


            # Create a data source.
            data_source = AIMindDataSource(
                engine="postgres",
                description="House sales data",
                connection_data={
                    'user': 'demo_user',
                    'password': 'demo_password',
                    'host': 'samples.mindsdb.com',
                    'port': 5432,
                    'database': 'demo',
                    'schema': 'demo_data'
                }
                tables=["house_sales"],
            )

            # Create the API wrapper.
            api_wrapper = AIMindAPIWrapper(
                datasources=[data_source]
            )

            # Create the tool.
            tool = AIMindTool(api_wrapper=api_wrapper)

    Invocation with args:
        .. code-block:: python

            tool.invoke({"query": "How many three-bedroom houses were sold in 2008?"})

        .. code-block:: python

            'The number of three-bedroom houses sold in 2008 was 8.'

    Invocation with ToolCall:

        .. code-block:: python

            tool.invoke({"args": {"query": "How many three-bedroom houses were sold in 2008?"}, "id": "1", "name": tool.name, "type": "tool_call"})

        .. code-block:: python

            ToolMessage(content='The query has been executed successfully. A total of 8 three-bedroom houses were sold in 2008.', name='ai_mind', tool_call_id='1')
    """  # noqa: E501
    name: str = "ai_mind"
    description: Text = (
        "A wrapper around [AI-Minds](https://mindsdb.com/minds). "
        "Useful for when you need answers to questions from your data, stored in "
        "data sources including PostgreSQL, MySQL, MariaDB, ClickHouse, Snowflake "
        "and Google BigQuery. "
        "Input should be a question in natural language."
    )
    api_wrapper: AIMindAPIWrapper

    def _run(
        self, query: Text, *, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        return self.api_wrapper.run(query)

    # TODO: Implement if tool has native async functionality, otherwise delete.

    # async def _arun(
    #     self,
    #     a: int,
    #     b: int,
    #     *,
    #     run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    # ) -> str:
    #     ...
