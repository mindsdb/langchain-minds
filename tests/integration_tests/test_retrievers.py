from typing import Type

from langchain_minds.retrievers import MindsRetriever
from langchain_tests.integration_tests import (
    RetrieversIntegrationTests,
)


class TestMindsRetriever(RetrieversIntegrationTests):
    @property
    def retriever_constructor(self) -> Type[MindsRetriever]:
        """Get an empty vectorstore for unit tests."""
        return MindsRetriever

    @property
    def retriever_constructor_params(self) -> dict:
        return {"k": 2}

    @property
    def retriever_query_example(self) -> str:
        """
        Returns a dictionary representing the "args" of an example retriever call.
        """
        return "example query"
