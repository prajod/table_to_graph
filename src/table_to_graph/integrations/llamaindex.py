"""
LlamaIndex Integration for Table-to-Graph

This module provides a LlamaIndex compatible BaseRetriever that wraps
the Table-to-Graph retrieval engine.
"""

from typing import Any

try:
    from llama_index.core.retrievers import BaseRetriever
    from llama_index.core.schema import NodeWithScore, QueryBundle, TextNode

    HAS_LLAMA_INDEX = True
except ImportError:

    class BaseRetriever:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    NodeWithScore = Any  # type: ignore
    TextNode = Any  # type: ignore
    QueryBundle = Any  # type: ignore
    HAS_LLAMA_INDEX = False

from table_to_graph.models import TableGraph
from table_to_graph.retrieval import ContextSerializer, GraphRetriever, GraphStore


class LlamaIndexTableGraphRetriever(BaseRetriever):
    """
    A LlamaIndex retriever that queries in-memory table graphs using Table-to-Graph.

    Given a list of TableGraph objects, this retriever acts natively within LlamaIndex
    Query Engines. It uses keyword/fuzzy matching to find relevant nodes and extracts
    the surrounding k-hop subgraph, returning it as a highly structured TextNode.
    """

    def __init__(
        self,
        graphs: list[TableGraph],
        top_k: int = 10,
        k_hops: int = 1,
        strategy: str = "node-centric",
        **kwargs: Any,
    ) -> None:
        """Initialize the TableGraphRetriever.

        Args:
            graphs: List of TableGraph objects to query.
            top_k: Maximum number of seed nodes to find.
            k_hops: Graph traversal depth from seed nodes.
            strategy: Serialization strategy ("node-centric", "edge-centric", "path-centric").
        """
        super().__init__(**kwargs)
        if not HAS_LLAMA_INDEX:
            raise ImportError("llama-index-core is required to use the LlamaIndex integration.")

        self.graphs = graphs
        self.top_k = top_k
        self.k_hops = k_hops
        self.strategy = strategy

        self._store = GraphStore()
        self._store.add_all(self.graphs)
        self._retriever = GraphRetriever(self._store, top_k=self.top_k, k_hops=self.k_hops)
        self._serializer = ContextSerializer(strategy=self.strategy)

    def _retrieve(self, query_bundle: QueryBundle) -> list[NodeWithScore]:
        """Retrieve relevant subgraphs and serialize them as a Node."""
        result = self._retriever.retrieve(query_bundle.query_str)

        if not result.subgraph or result.subgraph.number_of_nodes() == 0:
            return []

        context_str = self._serializer.serialize(result)

        # We return a single TextNode containing the cohesive subgraph context
        node = TextNode(
            text=context_str,
            metadata={
                "source": "table_to_graph",
                "strategy": self.strategy,
                "num_nodes": result.subgraph.number_of_nodes(),
            },
        )
        return [NodeWithScore(node=node, score=1.0)]
