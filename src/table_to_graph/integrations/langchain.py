"""
LangChain Integration for Table-to-Graph

This module provides a LangChain compatible BaseRetriever that wraps
the Table-to-Graph retrieval engine.
"""

from typing import Any

try:
    from langchain_core.callbacks import CallbackManagerForRetrieverRun
    from langchain_core.documents import Document
    from langchain_core.retrievers import BaseRetriever
    from pydantic import PrivateAttr

    HAS_LANGCHAIN = True
except ImportError:

    class BaseRetriever:  # type: ignore
        pass

    def PrivateAttr(*args: Any, **kwargs: Any) -> Any:  # type: ignore[no-redef]
        return None

    Document = Any  # type: ignore
    CallbackManagerForRetrieverRun = Any  # type: ignore
    HAS_LANGCHAIN = False

from table_to_graph.models import TableGraph
from table_to_graph.retrieval import ContextSerializer, GraphRetriever, GraphStore


class LangChainTableGraphRetriever(BaseRetriever):
    """
    A LangChain retriever that queries in-memory table graphs using Table-to-Graph.

    Given a list of TableGraph objects, this retriever acts natively within LangChain
    LCEL chains. It uses keyword/fuzzy matching to find relevant nodes and extracts
    the surrounding k-hop subgraph, returning it as a highly structured text Document.
    """

    graphs: list[TableGraph]
    top_k: int = 10
    k_hops: int = 1
    strategy: str = "node-centric"

    _store: GraphStore = PrivateAttr()
    _retriever: GraphRetriever = PrivateAttr()
    _serializer: ContextSerializer = PrivateAttr()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        if not HAS_LANGCHAIN:
            raise ImportError("langchain-core is required to use the LangChain integration.")

        self._store = GraphStore()
        self._store.add_all(self.graphs)
        self._retriever = GraphRetriever(self._store, top_k=self.top_k, k_hops=self.k_hops)
        self._serializer = ContextSerializer(strategy=self.strategy)

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        """Retrieve relevant subgraphs and serialize them as a Document."""
        result = self._retriever.retrieve(query)

        if not result.subgraph or result.subgraph.number_of_nodes() == 0:
            return []

        context_str = self._serializer.serialize(result)

        # Return a single synthesized Document containing the relevant subgraph context
        return [
            Document(
                page_content=context_str,
                metadata={
                    "source": "table_to_graph",
                    "strategy": self.strategy,
                    "num_nodes": result.subgraph.number_of_nodes(),
                },
            )
        ]
