"""Serializer registry for graph export formats."""

from table_to_graph.interfaces import Serializer
from table_to_graph.registry import Registry

serializer_registry: Registry[Serializer] = Registry[Serializer]("serializers")
