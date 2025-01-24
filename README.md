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

Set the password for our demo database as an environment variable.
```bash
export POSTGRES_PASSWORD=demo_password
```

OR

```python
import getpass
import os

if not os.environ.get("MINDS_API_KEY"):
    os.environ["MINDS_API_KEY"] = getpass.getpass("MINDS API key:\n")

if not os.environ.get("POSTGRES_PASSWORD"):
    os.environ["POSTGRES_PASSWORD"] = getpass.getpass("Postgres password:\n")
```

## Usage

The `AIMindTool` can be used to configure and query a [range of data sources](https://docs.mdb.ai/docs/data_sources) in plain English.

### Instantiation

```python
from langchain_minds import AIMindDataSource, AIMindEnvVar, AIMindAPIWrapper, AIMindTool


# Create a data source that your Mind will have access to.
# This will create a new data source using the connection data provided with the given name.
# To configure additional data sources, simply create additional instances of
# AIMindDataSource and pass it to the wrapper below.
datasource = AIMindDataSource(
    name="demo_datasource",
    description="house sales data",
    engine="postgres",
    connection_data={
        "user": 'demo_user',
        "password": AIMindEnvVar('POSTGRES_PASSWORD', is_secret=True), # Use an environment variable for the password.
        "host": "samples.mindsdb.com",
        "port": 5432,
        "database": "demo",
        "schema": "demo_data"
    },
    tables=['house_sales']
)

# NOTE: Feel free to use the above connection data as is! It's our demo database open to the public.
# The password is "demo_password".

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
```

### Invocation

```
# Invoke the tool by asking a question in plain English.
tool.invoke({"query": "How many three-bedroom houses were sold in 2008?"})
```
