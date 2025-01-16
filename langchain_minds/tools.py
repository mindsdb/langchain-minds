"""AIMind tool."""

import os
from typing import Any, Dict, List, Optional, Union

import openai
from langchain_core.callbacks import (
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.utils import convert_to_secret_str, get_from_dict_or_env
from minds.client import Client
from minds.datasources import DatabaseConfig
from minds.exceptions import ObjectNotFound
from pydantic import BaseModel, Field, SecretStr


class AIMindEnvVar:
    """
    The loader for environment variables used by the AIMindTool.
    """

    value: Union[str, SecretStr]

    def __init__(self, name: str, is_secret: bool = False) -> None:
        if is_secret:
            self.value = convert_to_secret_str(os.environ[name])
        else:
            self.value = os.environ[name]


class AIMindDataSource(BaseModel):
    """
    The configuration for data sources used by the AIMindTool.
    """

    name: str = Field(default=None, description="Name of the data source")
    minds_api_key: Optional[SecretStr] = Field(
        default=None, description="API key for the Minds API"
    )
    engine: Optional[str] = Field(
        default=None, description="Engine (type) of the data source"
    )
    description: Optional[str] = Field(
        default="", description="Description of the data contained in the data source"
    )
    connection_data: Optional[Dict[str, Any]] = Field(
        default={},
        description="Connection parameters to connect to the data source",
    )
    tables: Optional[List[str]] = Field(
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
        2. If the data source does not exist, the following are required:
            - name
            - engine
            - description
            - connection_data

        The tables are optional and can be provided if the data source does not exist.
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
                raise ValueError(
                    f"The data source with the name '{self.name}' already exists."
                    "Only the name is required to initialize an existing data source."
                )
        except ObjectNotFound:
            # If the parameters for creating the data source are not provided,
            # raise an error.
            if not self.engine or not self.description or not self.connection_data:
                raise ValueError(
                    "The required parameters for creating the data source are not"
                    " provided."
                )

        # Convert the parameters set as environment variables to the actual values.
        connection_data = {}
        for key, value in (self.connection_data or {}).items():
            if isinstance(value, AIMindEnvVar):
                connection_data[key] = (
                    value.value.get_secret_value()
                    if isinstance(value.value, SecretStr)
                    else value.value
                )
            else:
                connection_data[key] = value

        # Create the data source.
        minds_client.datasources.create(
            DatabaseConfig(
                name=self.name,
                engine=self.engine,
                description=self.description,
                connection_data=connection_data,
                tables=self.tables,
            )
        )


class AIMindAPIWrapper(BaseModel):
    """
    The API wrapper for the Minds API.
    """

    name: str = Field(description="Name of the Mind")
    minds_api_key: Optional[SecretStr] = Field(
        default=None, description="API key for the Minds API"
    )
    datasources: Optional[List[AIMindDataSource]] = Field(
        default=[], description="List of data sources to be accessible by the Mind"
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
        2. If the Mind does not exist, data sources are required.
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
                raise ValueError(
                    f"The Mind with the name '{self.name}' already exists."
                    "Only the name is required to initialize an existing Mind."
                )
        except ObjectNotFound:
            # If the data sources are not provided, raise an error.
            if not self.datasources:
                raise ValueError(
                    "At least one data source should be configured to create a Mind."
                )

        # Create the Mind.
        mind = minds_client.minds.create(name=self.name)

        # Add the data sources to the Mind.
        for data_source in self.datasources or []:
            mind.add_datasource(data_source.name)

    def run(self, query: str) -> str:
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
    """
    The AIMind tool.
    """

    name: str = "ai_mind"
    description: str = (
        "A wrapper around [AI-Minds](https://mindsdb.com/minds). "
        "Useful for when you need answers to questions from your data, stored in "
        "data sources including PostgreSQL, MySQL, MariaDB, ClickHouse, Snowflake "
        "and Google BigQuery. "
        "Input should be a question in natural language."
    )
    api_wrapper: AIMindAPIWrapper

    def _run(
        self, query: str, *, run_manager: Optional[CallbackManagerForToolRun] = None
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
