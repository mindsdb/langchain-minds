from importlib import metadata

from langchain_minds.toolkits import AIMindToolkit
from langchain_minds.tools import AIMindTool

try:
    __version__ = metadata.version(__package__)
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)

__all__ = [
    "AIMindToolkit",
    "AIMindTool",
    "__version__",
]
