"""
Test suite for the staggered alloy mix matrix benchmark.

Splits into two concerns:
1. PDF extraction: verify the generated staggered PDF can be read by the extractor.
2. Graph retrieval: verify the correctly-structured TableData (from the corpus)
   produces accurate retrieval for coordinate-style Q&A queries.

Note: PDF extraction of a staggered "dual-from / shared-to" layout is inherently
lossy — pdfplumber cannot reconstruct the multi-level header semantics from the
visual staggering. The retrieval tests therefore use the authoritative TableData
from create_benchmark_corpus() which has the correct header structure.
"""

import sys
from pathlib import Path

import pytest

# Add benchmarks dir to path so we can import corpus helpers
BENCHMARKS_DIR = Path(__file__).parent.parent / "benchmarks"
if str(BENCHMARKS_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARKS_DIR))

from table_to_graph import build_graph, classify_table, extract_tables
from table_to_graph.retrieval.context_serializer import ContextSerializer
from table_to_graph.retrieval.graph_store import GraphStore
from table_to_graph.retrieval.retriever import GraphRetriever

STAGGERED_PDF = BENCHMARKS_DIR / "benchmark_staggered_alloy_table.pdf"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def alloy_corpus_table():
    """Load the authoritative alloy_mix_matrix_option_a TableData from corpus."""
    from benchmarks.benchmark_retrieval import create_benchmark_corpus

    corpus = create_benchmark_corpus()
    table = corpus["alloy_mix_matrix_option_a"]
    # Classify so the builder knows it's a pivot
    classification = classify_table(table)
    table.metadata.classification = classification
    return table


@pytest.fixture(scope="module")
def alloy_retriever(alloy_corpus_table):
    """Build a GraphStore + GraphRetriever from the corpus alloy table."""
    graph = build_graph(alloy_corpus_table)
    store = GraphStore()
    store.add(graph)
    return GraphRetriever(store, top_k=8, k_hops=1)


# ── PDF Extraction Tests ───────────────────────────────────────────────────────


def test_staggered_alloy_pdf_exists():
    """PDF must have been generated before this test runs."""
    if not STAGGERED_PDF.exists():
        pytest.skip(
            f"Staggered alloy PDF not found at {STAGGERED_PDF}. "
            "Run: poetry run python benchmarks/generate_benchmark_pdfs.py"
        )
    assert STAGGERED_PDF.stat().st_size > 0


def test_staggered_alloy_pdf_extraction():
    """At least one table must be extractable from the generated PDF."""
    if not STAGGERED_PDF.exists():
        pytest.skip("Staggered alloy PDF not found — run generate_benchmark_pdfs.py first.")
    tables = extract_tables(str(STAGGERED_PDF), classify=False)
    assert len(tables) >= 1, "No tables extracted from staggered alloy PDF"
    # Must have rows with numeric-looking cell values
    all_values = [str(cell) for row in tables[0].rows for cell in row]
    numeric_vals = [v for v in all_values if v.replace(".", "").isdigit()]
    assert len(numeric_vals) > 0, "No numeric values extracted from staggered alloy table"


# ── Corpus TableData Tests ─────────────────────────────────────────────────────


def test_alloy_corpus_table_structure(alloy_corpus_table):
    """Corpus alloy table must have the expected multi-level header and row structure."""
    assert len(alloy_corpus_table.headers) == 3, (
        f"Expected 3 header levels, got {len(alloy_corpus_table.headers)}"
    )
    assert len(alloy_corpus_table.rows) == 3, (
        f"Expected 3 data rows, got {len(alloy_corpus_table.rows)}"
    )


def test_alloy_corpus_classification(alloy_corpus_table):
    """Corpus alloy table must classify as 'pivot' archetype."""
    classification = classify_table(alloy_corpus_table)
    assert classification.table_type == "pivot", (
        f"Expected 'pivot', got '{classification.table_type}'"
    )


def test_alloy_corpus_graph_built(alloy_corpus_table):
    """Graph built from corpus table must have Measure nodes (not just Dimensions)."""
    graph = build_graph(alloy_corpus_table)
    # Nodes store their type under the 'label' key (set by add_node in base.py)
    node_labels = {data.get("label") for _, data in graph.graph.nodes(data=True)}
    assert graph.graph.number_of_nodes() > 0, "Graph is empty"
    assert "Measure" in node_labels, (
        f"Expected Measure nodes in graph, found node labels: {node_labels}"
    )


# ── Retrieval Q&A Tests ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "query_text,expected_token",
    [
        # Queries match benchmark_retrieval.py Q102-Q110
        (
            "What is the part creation value for copper mix 10 to 20 and tin mix 36.5 to 50.0?",
            "17.44",
        ),
        (
            "What is the part creation value for copper mix 20 to 30 and tin mix 50.0 to 60.0?",
            "25.30",
        ),
        (
            "What is the part creation value for copper mix 30 to 40 and tin mix 60.0 to 70.0?",
            "34.50",
        ),
        (
            "What is the part creation value for copper mix 30 to 40 and tin mix 70.0 to 80.0?",
            "40.10",
        ),
        (
            "What is the part creation value for copper mix 10 to 20 and tin mix 60.0 to 70.0?",
            "28.10",
        ),
        (
            "What is the part creation value for copper mix 20 to 30 and tin mix 70.0 to 80.0?",
            "35.60",
        ),
    ],
)
def test_alloy_corpus_retrieval(alloy_retriever, query_text, expected_token):
    """Each alloy mix coordinate query must return the correct value token in context."""
    serializer = ContextSerializer(strategy="node-centric")
    result = alloy_retriever.retrieve(query_text)

    assert result.subgraph.number_of_nodes() > 0, (
        f"Retriever returned empty subgraph for: '{query_text}'"
    )

    context = serializer.serialize(result)
    assert expected_token in context, (
        f"Expected token '{expected_token}' not found for query: '{query_text}'\n"
        f"Serialized context:\n{context}"
    )
