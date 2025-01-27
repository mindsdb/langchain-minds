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

Given below is an example that demonstrates how to configure our demo PostgreSQL database, which contains house sales data, and find out how many three-bedroom houses were sold in 2008.

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
        "password": AIMindEnvVar(
            'POSTGRES_PASSWORD',
            is_secret=True
        ), # Use an environment variable for the password.
        "host": "samples.mindsdb.com",
        "port": 5432,
        "database": "demo",
        "schema": "demo_data"
    },
    tables=['house_sales']
)

# NOTE: Feel free to use the above connection data as is!
# It's our demo database open to the public.

# To re-use an existing data source, simply provide the name of the data source
# without any other parameters.
# datasource = AIMindDataSource(
#     name="demo_datasource",
# )

# Create the wrapper for the Minds API by giving the Mind a name and passing in the
# data sources created above.
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
ai_minds_tool = AIMindTool(
    api_wrapper=api_wrapper
)
```

### Invocation

```python
# Invoke the tool by asking a question in plain English.
ai_minds_tool.invoke({"query": "How many three-bedroom houses were sold in 2008?"})
>> 'The number of three-bedroom houses sold in 2008 was 8.'
```

## Usage with an Agent

Given below is an example that uses the `AIMindTool` configured above and a tool that searches the web (`BraveSearch`) to find the total number of houses sold in 2008 and compare the average prices of these houses to the average house price in the US today.

```python
from langchain import hub
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_community.tools import BraveSearch
from langchain_openai import ChatOpenAI


llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)

search = BraveSearch.from_api_key(api_key=BRAVE_SEARCH_API_KEY, search_kwargs={"count": 3})

tools = [search, database]

prompt = hub.pull("hwchase17/openai-functions-agent")

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

agent_executor.invoke(
    {
        "input": "According to the data in my database, how many houses in total were sold in 2008?"
        "Compare the average price of the houses that were sold to the approximate average house price today in the US."
    }
)
>> Entering new AgentExecutor chain...
>>
>> Invoking: `ai_mind` with `{'query': 'How many houses were sold in 2008 and what was the average price of those houses?'}`
>>
>>
>> In 2008, a total of 28 houses were sold. The average price of these houses was approximately 484,930.14.
>> Invoking: `brave_search` with `{'query': 'approximate average house price in the US today'}`
>>
>>
>> [{"title": "Average House Price by State in 2024 | The Motley Fool", "link": "https://www.fool.com/the-ascent/research/>> average-house-price-state/", "snippet": "The average house price in the United States as of the third quarter of 2024 is >> <strong>$420,400</strong>. See how states compare here."}, {"title": "Average new home sales price in the U.S. 2023 | Statista", >> "link": "https://www.statista.com/statistics/240991/average-sales-prices-of-new-homes-sold-in-the-us/", "snippet": "After a dramatic >> increase in 2022, the average sales price of a new home in the United States dropped slightly in 2023 from 540,000 to <strong>511,>> 100 U.S.</strong>"}, {"title": "Median Home Price By State: How Much Houses Cost | Bankrate", "link": "https://www.bankrate.com/>> real-estate/median-home-price/", "snippet": "Another useful guideline that can help is the 28 percent rule: Many experts advise >> limiting your housing expenses to <strong>no more than 28 percent of your income</strong>. If you earn $7,000 per month, for >> example, that means keeping your total housing costs at $1,960 or less."}]The approximate average house price in the US today is >> $420,400.
>>
>> Comparing this to the average price of houses sold in 2008, which was approximately $484,930.14, we can see that the average house >> price in 2008 was higher than the approximate average house price today in the US.
```
