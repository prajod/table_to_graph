from typing import Any

from table_to_graph.interfaces import (
    DocumentReader,
    GraphBuilder,
    Normalizer,
    Serializer,
    TableClassifier,
    TableExtractor,
)


def test_table_extractor_protocol():
    class ValidExtractor:
        def extract(self, source: Any) -> list[Any]:
            return []

        def can_handle(self, source: Any) -> bool:
            return True

    class InvalidExtractor:
        def extract(self, source: Any) -> list[Any]:
            return []

        # Missing can_handle

    assert isinstance(ValidExtractor(), TableExtractor)
    assert not isinstance(InvalidExtractor(), TableExtractor)


def test_document_reader_protocol():
    class ValidReader:
        def read(self, source: Any) -> list[Any]:
            return []

        def supported_extensions(self) -> list[str]:
            return []

    assert isinstance(ValidReader(), DocumentReader)


def test_table_classifier_protocol():
    class ValidClassifier:
        def classify(self, table: Any) -> Any:
            pass

    assert isinstance(ValidClassifier(), TableClassifier)


def test_graph_builder_protocol():
    class ValidBuilder:
        def build(self, table: Any, classification: Any) -> Any:
            pass

        def supported_types(self) -> list[str]:
            return []

    assert isinstance(ValidBuilder(), GraphBuilder)


def test_serializer_protocol():
    class ValidSerializer:
        def serialize(self, graph: Any) -> str:
            return ""

        def format_name(self) -> str:
            return "test"

    assert isinstance(ValidSerializer(), Serializer)


def test_normalizer_protocol():
    class ValidNormalizer:
        def normalize(self, table: Any) -> Any:
            pass

    assert isinstance(ValidNormalizer(), Normalizer)
