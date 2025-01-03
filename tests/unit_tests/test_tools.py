from typing import Type
from unittest.mock import MagicMock, patch

from langchain_tests.unit_tests import ToolsUnitTests

from langchain_minds import AIMindAPIWrapper, AIMindDataSource, AIMindTool


class TestAIMindToolUnit(ToolsUnitTests):
    @property
    def tool_constructor(self) -> Type[AIMindTool]:
        return AIMindTool

    @property
    def tool_constructor_params(self) -> dict:
        datasource = AIMindDataSource(
            description="house sales",
            engine="postgres",
            connection_data={
                "user": "demo_user",
                "password": "demo_password",
                "host": "samples.mindsdb.com",
                "port": 5432,
                "database": "demo",
                "schema": "demo_data",
            },
            tables=["house_sales"],
        )

        with patch("langchain_minds.tools.Client") as mock_minds_client:
            mock_minds_client.minds.create.return_value = MagicMock()
            api_wrapper = AIMindAPIWrapper(datasources=[datasource])

        return {"api_wrapper": api_wrapper}

    @property
    def tool_invoke_params_example(self) -> dict:
        """
        Returns a dictionary representing the "args" of an example tool call.
        """
        return {"query": "How many three-bedroom houses were sold in 2008?"}
