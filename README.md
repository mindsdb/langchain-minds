# langchain-minds

This package contains the LangChain adapter for [Minds](https://mindsdb.com/minds).

## Installation

```bash
pip install -U langchain-minds
```

## Setup

Login to your Minds account at https://mdb.ai and obtain an API key and set it as an environment variable.

```bash
export MINDS_API_KEY=<YOUR_API_KEY>
```

OR

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
# This will create a new data source using the connection data provided with the given name.
# To configure additional data sources, simply create additional instances of
# AIMindDataSource and pass it to the wrapper below.
datasource = AIMindDataSource(
    name="demo_datasource",
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

# To re-use an existing data source, simply provide the name of the data source without any other parameters.
# datasource = AIMindDataSource(
#     name="demo_datasource",
# )

# Create the wrapper for the Minds API by giving the Mind a name and passing in the data sources created above.
# This will create a new Mind with the given name and access to the data sources.
api_wrapper = AIMindAPIWrapper(
    name="demo_mind",
    datasources=[datasource]
)

# To re-use an existing Mind, simply provide the name of the Mind without any data sources.
# aimind_tool = AIMindAPIWrapper(
#     name="demo_mind",
# )

# Create the tool by simply passing in the API wrapper from before.
tool = AIMindTool(
    api_wrapper=api_wrapper
)

# Invoke the tool by asking a question in plain English.
tool.invoke({"query": "How many three-bedroom houses were sold in 2008?"})
```
