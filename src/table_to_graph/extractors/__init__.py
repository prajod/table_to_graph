from table_to_graph.interfaces import TableExtractor
from table_to_graph.registry import Registry

extractor_registry = Registry[TableExtractor]("extractors")

# Note: Individual extractors must be imported elsewhere (e.g. in the top-level __init__)
# to trigger their decorators and register them.
