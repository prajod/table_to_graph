import pandas as pd
import pytest

from table_to_graph import (
    build_graph,
    extract_tables,
    retrieve_context,
)
from table_to_graph import (
    table_to_graph as serialize_table_to_graph,
)


def _sample_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Property": ["Processor", "Memory"],
            "Value": ["Intel Core i9", "32GB DDR5"],
        }
    )


def test_table_to_graph_facade_serializes_markdown() -> None:
    output = serialize_table_to_graph(_sample_dataframe(), format="markdown")

    assert "Processor" in output
    assert "Intel Core i9" in output


def test_retrieve_context_facade_returns_relevant_evidence() -> None:
    tables = extract_tables(_sample_dataframe(), classify=True)
    graphs = [build_graph(table) for table in tables]

    context = retrieve_context(graphs, "Which processor is configured?", top_k=2, k_hops=1)

    assert "Processor" in context
    assert "Intel Core i9" in context


def test_extract_tables_rejects_unsupported_source() -> None:
    with pytest.raises(ValueError, match="No suitable extractor"):
        extract_tables(object())
