from typing import Type

from langchain_tests.integration_tests import ToolsIntegrationTests

from langchain_minds import AIMindAPIWrapper, AIMindDataSource, AIMindTool


class TestAIMindToolIntegration(ToolsIntegrationTests):
    @property
    def tool_constructor(self) -> Type[AIMindTool]:
        return AIMindTool

    @property
    def tool_constructor_params(self) -> dict:
        datasource = AIMindDataSource(
            name="test_datasource",
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
        api_wrapper = AIMindAPIWrapper(name="test_mind", datasources=[datasource])
        return {"api_wrapper": api_wrapper}

    @property
    def tool_invoke_params_example(self) -> dict:
        """
        Returns a dictionary representing the "args" of an example tool call.
        """
        return {"query": "How many three-bedroom houses were sold in 2008?"}
