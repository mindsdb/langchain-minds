# langchain-minds

This package contains the LangChain integration with Minds

## Installation

```bash
pip install -U langchain-minds
```

And you should configure credentials by setting the following environment variables:

* TODO: fill this out

## Chat Models

`ChatMinds` class exposes chat models from Minds.

```python
from langchain_minds import ChatMinds

llm = ChatMinds()
llm.invoke("Sing a ballad of LangChain.")
```

## Embeddings

`MindsEmbeddings` class exposes embeddings from Minds.

```python
from langchain_minds import MindsEmbeddings

embeddings = MindsEmbeddings()
embeddings.embed_query("What is the meaning of life?")
```

## LLMs
`MindsLLM` class exposes LLMs from Minds.

```python
from langchain_minds import MindsLLM

llm = MindsLLM()
llm.invoke("The meaning of life is")
```
