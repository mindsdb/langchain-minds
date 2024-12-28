# langchain-minds

This package contains the LangChain adapter for [Minds](https://mindsdb.com/minds).

## Installation

```bash
pip install -U langchain-minds
```

# Setup

```python
import getpass
import os

if not os.environ.get("MINDS_API_KEY"):
    os.environ["MINDS_API_KEY"] = getpass.getpass("MINDS API key:\n")
```

## Usage

The `AIMindTool` can be used to configure and query a [range of data sources](https://docs.mdb.ai/docs/data_sources) in plain English.

```python
from langchain_minds import AIMindDataSource, AIMindAPIWrapper, AIMindTool


# Create a data source that your Mind will have access to.
# To configure additional data sources, simply create additional instances of AIMindDataSource and pass it to the wrapper below.
datasource = AIMindDataSource(
    description='house sales data',
    engine='postgres',
    connection_data={
        'user': 'demo_user',
        'password': 'demo_password',
        'host': 'samples.mindsdb.com',
        'port': 5432,
        'database': 'demo',
        'schema': 'demo_data'
    },
    tables=['house_sales']
)

# Create the wrapper for the Minds API by passing in the data sources created above.
api_wrapper = AIMindAPIWrapper(
    datasources=[datasource]
)

# Create the tool by simply passing in the API wrapper from before.
tool = AIMindTool(
    api_wrapper=api_wrapper
)
```
