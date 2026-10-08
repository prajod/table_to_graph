import pytest

from table_to_graph.classifiers.features import TableFeatures
from table_to_graph.classifiers.heuristic_classifier import HeuristicTableClassifier
from table_to_graph.models import TableData


@pytest.fixture
def classifier():
    return HeuristicTableClassifier()


def test_classify_key_value(classifier):
    table = TableData(
        headers=[["Property", "Value"]],
        rows=[["CPU:", "i9-13900K"], ["RAM:", "64GB DDR5"], ["Storage:", "2TB NVMe"]],
    )
    result = classifier.classify(table)
    assert result.table_type == "key_value"
    assert result.confidence > 0.5


def test_classify_comparison(classifier):
    table = TableData(
        headers=[["Feature", "Product A", "Product B", "Product C"]],
        rows=[
            ["Price", "$10", "$20", "$30"],
            ["Weight", "1kg", "2kg", "3kg"],
            ["Color", "Red", "Blue", "Green"],
        ],
    )
    result = classifier.classify(table)
    assert result.table_type == "comparison"
    assert result.confidence > 0.5


def test_classify_time_series(classifier):
    table = TableData(
        headers=[["Metric", "Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"]],
        rows=[["Revenue", "1000", "1100", "1200", "1300"], ["Profit", "200", "220", "240", "260"]],
    )
    result = classifier.classify(table)
    assert result.table_type == "time_series"
    assert result.confidence > 0.5


def test_classify_hierarchical(classifier):
    """Hierarchical tables are identified by indentation in col0 (tree structure).
    Note: Multi-level headers alone are NOT sufficient — they overlap with pivot.
    """
    table = TableData(
        headers=[["Account", "Debit ($)", "Credit ($)"]],
        rows=[
            ["1000 - Assets", "1,500,000", ""],
            ["  1100 - Current Assets", "800,000", ""],
            ["    1110 - Cash in Bank", "500,000", ""],
            ["    1120 - Accounts Receivable", "300,000", ""],
            ["  1200 - Fixed Assets", "700,000", ""],
        ],
    )
    result = classifier.classify(table)
    assert result.table_type == "hierarchical"
    assert result.confidence > 0.4


def test_classify_matrix(classifier):
    table = TableData(
        headers=[["", "City A", "City B", "City C"]],
        rows=[
            ["City A", "0", "10", "20"],
            ["City B", "10", "0", "15"],
            ["City C", "20", "15", "0"],
        ],
    )
    result = classifier.classify(table)
    assert result.table_type == "matrix"
    assert result.confidence > 0.5


def test_classify_relational(classifier):
    table = TableData(
        headers=[["id", "user_id", "order_date", "total"]],
        rows=[
            ["1", "u100", "2024-01-01", "50.00"],
            ["2", "u101", "2024-01-02", "75.50"],
            ["3", "u100", "2024-01-03", "20.00"],
        ],
    )
    result = classifier.classify(table)
    assert result.table_type == "relational"
    assert result.confidence > 0.5


def test_classify_pivot(classifier):
    table = TableData(
        headers=[["Category", "2023", "2023", "2024", "2024"], ["", "Q1", "Q2", "Q1", "Q2"]],
        rows=[
            ["Electronics", "500", "600", "550", "650"],
            ["Clothing", "300", "310", "320", "330"],
        ],
    )
    result = classifier.classify(table)
    assert result.table_type == "pivot"
    assert result.confidence > 0.5


def test_confidence_scores_in_metadata(classifier):
    table = TableData(headers=[["A", "B"]], rows=[["1", "2"]])
    result = classifier.classify(table)
    assert "scores" in result.metadata
    assert len(result.metadata["scores"]) == 7  # all 7 rules ran


def test_secondary_types_populated(classifier):
    # A generic table that might trigger multiple weak rules
    table = TableData(headers=[["Col1", "Col2", "Col3"]], rows=[["A", "B", "C"], ["D", "E", "F"]])
    # Lower fallback threshold to force secondary types
    classifier.fallback_threshold = 0.05
    result = classifier.classify(table)
    assert isinstance(result.secondary_types, list)
    # Even if empty, it should be a list, but likely has some fallbacks at 0.05


def test_empty_table_classification(classifier):
    table = TableData(headers=[], rows=[])
    result = classifier.classify(table)
    assert result.table_type == "unknown"
    assert result.confidence == 0.0


def test_custom_rule_injection():
    class DummyRule:
        name = "dummy"

        def evaluate(self, table: TableData, features: TableFeatures) -> float:
            return 0.99

    custom_classifier = HeuristicTableClassifier(rules=[DummyRule()])
    table = TableData(headers=[["A"]], rows=[["1"]])
    result = custom_classifier.classify(table)

    assert result.table_type == "dummy"
    assert result.confidence == 0.99
    assert len(result.metadata["scores"]) == 1
