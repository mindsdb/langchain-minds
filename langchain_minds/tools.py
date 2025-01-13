"""AIMind tool."""

from typing import Any, Dict, List, Optional, Text

import openai
from langchain_core.callbacks import (
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.utils import convert_to_secret_str, get_from_dict_or_env
from minds.client import Client
from minds.exceptions import ObjectNotFound
from pydantic import BaseModel, Field, SecretStr


class AIMindDataSource(BaseModel):
    """
    The configuration for data sources used by the AIMindTool.
    """

    name: Text = Field(default=None, description="Name of the data source")
    minds_api_key: SecretStr = Field(default=None, description="API key for the Minds API")
    engine: Optional[Text] = Field(description="Engine (type) of the data source")
    description: Optional[Text] = Field(
        description="Description of the data contained in the data source"
    )
    connection_data: Optional[Dict[Text, Any]] = Field(
        description="Connection parameters to establish a connection to the data source"
    )
    tables: Optional[List[Text]] = Field(
        default=[],
        description="List of tables from the data source to be accessible by the Mind",
    )

    def __init__(self, **data: Any) -> None:
        """
        Initializes the data source configuration.
        Validates the API key is available and the name is set.
        Creates the data source if it does not exist.

        There are two ways to initialize the data source:
        1. If the data source already exists, only the name is required.
        2. If the data source does not exist, the engine, description and connection_data are required.
        """
        super().__init__(**data)

        # Validate that the API key is provided.
        self.minds_api_key = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "minds_api_key",
                "MINDS_API_KEY",
            )
        )

        # Create a Minds client.
        minds_client = Client(
            self.minds_api_key.get_secret_value(),
            # self.minds_api_base
        )

        # Check if the data source already exists.
        try:
            if minds_client.datasources.get(self.name):
                # TODO: If the data source already exists and the other parameters are provided,
                # what should happen?
                # Update the data source?
                # Ignore them and use just the name?
                return
        except ObjectNotFound:
            # If the parameters for creating the data source are not provided, raise an error.
            if not self.engine or not self.description or not self.connection_data:
                raise ValueError(
                    "The required parameters for creating the data source are not provided."
                )

        # Create the data source.
        minds_client.datasources.create(
            name=self.name,
            engine=self.engine,
            description=self.description,
            connection_data=self.connection_data,
            tables=self.tables,
        )


class AIMindAPIWrapper(BaseModel):
    """
    The API wrapper for the Minds API.
    """

    name: Text = Field(description="Name of the Mind")
    minds_api_key: SecretStr = Field(default=None, description="API key for the Minds API")
    datasources: Optional[List[AIMindDataSource]] = Field(
        default=[],
        description="List of data sources to be accessible by the Mind"
    )

    # Not set by the user, but used internally.
    openai_client: Any = Field(default=None, exclude=True)

    def __init__(self, **data: Any) -> None:
        """
        Initializes the API wrapper for the Minds API.
        Validates the API key is available and the name is set.
        Creates the Mind and adds the data sources to it.
        Initializes the OpenAI client used to interact with the created Mind.

        There are two ways to initialize the API wrapper:
        1. If the Mind already exists, only the name is required.
        2. If the Mind does not exist, the data sources are required.
        """
        super().__init__(**data)

        # Validate that the API key is provided.
        self.minds_api_key = convert_to_secret_str(
            get_from_dict_or_env(
                data,
                "minds_api_key",
                "MINDS_API_KEY",
            )
        )

        # Create an OpenAI client to run queries against the Mind.
        self.openai_client = openai.OpenAI(
            api_key=self.minds_api_key.get_secret_value(), base_url="https://mdb.ai/"
        ).chat.completions

        # Create a Minds client.
        minds_client = Client(
            self.minds_api_key.get_secret_value(),
            # self.minds_api_base
        )

        # Check if the Mind already exists.
        try:
            if minds_client.minds.get(self.name):
                # TODO: If the Mind already exists and data sources are provided, what should happen?
                # Add the new data sources?
                # Replace the existing data sources?
                return
        except ObjectNotFound:
            # If the data sources are not provided, raise an error.
            if not self.datasources:
                raise ValueError("At least one data source should be configured.")

        # Create the Mind.
        mind = minds_client.minds.create(name=self.name)

        # Add the data sources to the Mind.
        for data_source in self.datasources:
            mind.add_datasource(data_source.name)

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
