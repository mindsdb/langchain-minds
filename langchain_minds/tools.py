"""AIMind tool."""

import secrets
from typing import Any, Dict, List, Optional, Text

import openai
from langchain_core.callbacks import (
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.utils import convert_to_secret_str, get_from_dict_or_env
from minds.client import Client
from minds.datasources import DatabaseConfig
from pydantic import BaseModel, Field, SecretStr
from langchain_minds.datasources import AIMindDataSource


class AIMindAPIWrapper(BaseModel):
    """
    The API wrapper for the Minds API.
    """

    name: Optional[Text] = Field(default=None)
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

        # Create an OpenAI client to run queries against the Mind.
        self.openai_client = openai.OpenAI(
            api_key=self.minds_api_key.get_secret_value(), base_url="https://mdb.ai/"
        ).chat.completions

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
        minds_client.minds.create(name=self.name, datasources=datasources, replace=True)

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


            # Create a data source that your Mind will have access to.
            # To configure additional data sources, simply create additional instances of AIMindDataSource and pass it to the wrapper below.
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

            # Create the wrapper for the Minds API by passing in the data sources created above.
            api_wrapper = AIMindAPIWrapper(
                datasources=[data_source]
            )

            # Create the tool by simply passing in the API wrapper from before.
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
