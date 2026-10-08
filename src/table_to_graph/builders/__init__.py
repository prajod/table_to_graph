"""Graph builder registry and base utilities.

Each builder converts a classified TableData into a typed NetworkX graph
wrapped in a TableGraph Pydantic model.
"""

from table_to_graph.interfaces import GraphBuilder
from table_to_graph.registry import Registry

builder_registry: Registry[GraphBuilder] = Registry[GraphBuilder]("builders")
