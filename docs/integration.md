# Integration & Pluggability Guide

`table-to-graph` is designed to be highly modular. Whether you want to use the full end-to-end PDF-to-Graph pipeline, or just extract DataFrames, or plug our retrieval engine directly into your existing LangChain/LlamaIndex apps, this guide shows you how.

## 1. Pluggable Table Extraction

If you just want high-quality table extraction from PDFs without building graphs, you can use the extraction layer directly. It handles multi-page continuations, merged cell unspooling, and normalization.

```python
from table_to_graph import extract_tables

# Extract tables from a PDF
tables = extract_tables("path/to/document.pdf")

for table in tables:
    print(f"Table on page {table.metadata.page_number}")
    print(f"Headers: {table.headers}")
    
    # Access the raw 2D grid
    for row in table.rows:
        print(row)
        
    # Or easily convert to a Pandas DataFrame
    df = table.to_dataframe()
    print(df.head())
```

## 2. Pluggable Classification

Want to intelligently route tables in your own pipeline based on their structural archetype? You can use our heuristic 7-archetype classifier directly on any `TableData` object.

```python
from table_to_graph import extract_tables, classify_table

tables = extract_tables("path/to/document.pdf")

for table in tables:
    # Get the classification (e.g., 'key_value', 'pivot', 'hierarchical')
    result = classify_table(table)
    
    print(f"Detected Type: {result.table_type}")
    print(f"Confidence: {result.confidence}")
    
    if result.table_type == 'pivot':
        route_to_complex_processor(table)
    elif result.table_type == 'key_value':
        route_to_metadata_extractor(table)
```

## 3. Pluggable Graph Generation (From CSV/DataFrames)

You don't have to start from a PDF! If you already have tables extracted as Pandas DataFrames or CSV files, you can inject them directly into the graph builders.

```python
import pandas as pd
from table_to_graph import extract_tables, build_graph

# Your existing tabular data
df = pd.read_csv("sales_data.csv")

# 1. 'extract_tables' natively accepts DataFrames!
tables = extract_tables(df, classify=True)
table_data = tables[0]

# 2. Build the NetworkX Graph
graph = build_graph(table_data)

print(f"Graph nodes: {graph.nx_graph.number_of_nodes()}")
print(f"Graph edges: {graph.nx_graph.number_of_edges()}")
```

## 4. Framework Adapters (LangChain & LlamaIndex)

The true power of `table-to-graph` is dropping it into your existing RAG workflows. We provide native Retrievers for the most popular frameworks.

### LangChain Integration

Use `LangChainTableGraphRetriever` to seamlessly insert table-to-graph retrieval into your LCEL chains.

```python
from table_to_graph import extract_tables, build_graph
from table_to_graph.integrations.langchain import LangChainTableGraphRetriever

# 1. Prepare your graphs
tables = extract_tables("financial_report.pdf", classify=True)
graphs = [build_graph(t) for t in tables]

# 2. Instantiate the LangChain Retriever
retriever = LangChainTableGraphRetriever(
    graphs=graphs,
    top_k=10,
    k_hops=1,
    strategy="node-centric"
)

# 3. Use natively in LCEL
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough

prompt = PromptTemplate.from_template(
    "Use the following table context to answer the question:\n{context}\n\nQuestion: {question}"
)
llm = ChatOpenAI(model="gpt-4")

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
)

response = chain.invoke("What were the H1 sales for the European region?")
print(response.content)
```

### LlamaIndex Integration

Use `LlamaIndexTableGraphRetriever` to inject table graphs into your LlamaIndex Query Engines.

```python
from table_to_graph import extract_tables, build_graph
from table_to_graph.integrations.llamaindex import LlamaIndexTableGraphRetriever
from llama_index.core import RetrieverQueryEngine

# 1. Prepare your graphs
tables = extract_tables("financial_report.pdf", classify=True)
graphs = [build_graph(t) for t in tables]

# 2. Instantiate the LlamaIndex Retriever
retriever = LlamaIndexTableGraphRetriever(
    graphs=graphs,
    top_k=10,
    k_hops=1
)

# 3. Create a standard Query Engine
query_engine = RetrieverQueryEngine.from_args(retriever)

# 4. Query
response = query_engine.query("What were the H1 sales for the European region?")
print(str(response))
```
