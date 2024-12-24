from importlib import metadata

from langchain_minds.chat_models import ChatMinds
from langchain_minds.document_loaders import MindsLoader
from langchain_minds.embeddings import MindsEmbeddings
from langchain_minds.retrievers import MindsRetriever
from langchain_minds.toolkits import MindsToolkit
from langchain_minds.tools import MindsTool
from langchain_minds.vectorstores import MindsVectorStore

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)

__all__ = [
    "ChatMinds",
    "MindsVectorStore",
    "MindsEmbeddings",
    "MindsLoader",
    "MindsRetriever",
    "MindsToolkit",
    "MindsTool",
    "__version__",
]
