from table_to_graph.interfaces import TableClassifier
from table_to_graph.registry import Registry

classifier_registry = Registry[TableClassifier]("classifiers")
