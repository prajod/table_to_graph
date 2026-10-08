from pathlib import Path

import pytest

from table_to_graph import extract_tables

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def ensure_fixtures():
    """Ensure fixtures are present before running tests."""
    pdf_files = list(FIXTURES_DIR.glob("*.pdf"))
    if len(pdf_files) < 10:
        import subprocess
        import sys

        # Run generator if not yet created
        create_script = FIXTURES_DIR / "create_fixtures.py"
        if create_script.exists():
            subprocess.run([sys.executable, str(create_script)], check=True)


def test_extract_and_classify_key_value_pdf(ensure_fixtures):
    pdf_path = FIXTURES_DIR / "archetype_01_key_value_specs_and_configs_10_tables.pdf"
    if not pdf_path.exists():
        pytest.skip("Fixture not yet generated")

    tables = extract_tables(str(pdf_path), classify=True)
    assert len(tables) >= 5, f"Expected multiple tables extracted, got {len(tables)}"

    # Check that majority are identified as key_value
    kv_count = sum(
        1
        for t in tables
        if getattr(t.metadata, "classification", None)
        and t.metadata.classification.table_type == "key_value"
    )
    assert kv_count >= len(tables) * 0.5, (
        f"Expected majority key_value, got {kv_count}/{len(tables)}"
    )


def test_extract_and_classify_comparison_pdf(ensure_fixtures):
    pdf_path = FIXTURES_DIR / "archetype_02_comparison_products_and_features_10_tables.pdf"
    if not pdf_path.exists():
        pytest.skip("Fixture not yet generated")

    tables = extract_tables(str(pdf_path), classify=True)
    assert len(tables) >= 5
    comp_count = sum(
        1
        for t in tables
        if getattr(t.metadata, "classification", None)
        and t.metadata.classification.table_type == "comparison"
    )
    assert comp_count >= len(tables) * 0.5


def test_extract_and_classify_time_series_pdf(ensure_fixtures):
    pdf_path = FIXTURES_DIR / "archetype_03_time_series_financial_and_metrics_10_tables.pdf"
    if not pdf_path.exists():
        pytest.skip("Fixture not yet generated")

    tables = extract_tables(str(pdf_path), classify=True)
    assert len(tables) >= 5
    ts_count = sum(
        1
        for t in tables
        if getattr(t.metadata, "classification", None)
        and t.metadata.classification.table_type == "time_series"
    )
    assert ts_count >= len(tables) * 0.5


def test_extract_and_classify_hierarchical_pdf(ensure_fixtures):
    """Known limitation: fpdf2 strips leading whitespace in cells, destroying the
    indentation signal that is the primary differentiator between hierarchical and
    pivot tables. Tables with multi-level headers but no indentation are structurally
    identical to pivot/cross-tab tables.

    We verify that 'hierarchical' appears as either the primary or secondary
    classification for a meaningful portion of tables.
    """
    pdf_path = FIXTURES_DIR / "archetype_04_hierarchical_org_and_nested_headers_10_tables.pdf"
    if not pdf_path.exists():
        pytest.skip("Fixture not yet generated")

    tables = extract_tables(str(pdf_path), classify=True)
    assert len(tables) >= 5

    # Count tables where hierarchical is primary OR a strong secondary
    hier_count = 0
    for t in tables:
        cls = getattr(t.metadata, "classification", None)
        if cls is None:
            continue
        if cls.table_type == "hierarchical" or "hierarchical" in (cls.secondary_types or []):
            hier_count += 1
    assert hier_count >= len(tables) * 0.5, (
        f"Expected hierarchical as primary/secondary in majority, got {hier_count}/{len(tables)}"
    )


def test_extract_and_classify_matrix_pdf(ensure_fixtures):
    pdf_path = FIXTURES_DIR / "archetype_05_matrix_adjacency_and_correlations_10_tables.pdf"
    if not pdf_path.exists():
        pytest.skip("Fixture not yet generated")

    tables = extract_tables(str(pdf_path), classify=True)
    assert len(tables) >= 5
    mat_count = sum(
        1
        for t in tables
        if getattr(t.metadata, "classification", None)
        and t.metadata.classification.table_type == "matrix"
    )
    assert mat_count >= len(tables) * 0.5


def test_extract_and_classify_relational_pdf(ensure_fixtures):
    pdf_path = FIXTURES_DIR / "archetype_06_relational_database_records_and_fks_10_tables.pdf"
    if not pdf_path.exists():
        pytest.skip("Fixture not yet generated")

    tables = extract_tables(str(pdf_path), classify=True)
    assert len(tables) >= 5
    rel_count = sum(
        1
        for t in tables
        if getattr(t.metadata, "classification", None)
        and t.metadata.classification.table_type == "relational"
    )
    assert rel_count >= len(tables) * 0.5


def test_extract_and_classify_pivot_pdf(ensure_fixtures):
    pdf_path = FIXTURES_DIR / "archetype_07_pivot_crosstab_and_breakdowns_20_tables.pdf"
    if not pdf_path.exists():
        pytest.skip("Fixture not yet generated")

    tables = extract_tables(str(pdf_path), classify=True)
    assert len(tables) >= 5
    pivot_count = sum(
        1
        for t in tables
        if getattr(t.metadata, "classification", None)
        and t.metadata.classification.table_type == "pivot"
    )
    assert pivot_count >= len(tables) * 0.5


def test_extract_mixed_diagram_part1(ensure_fixtures):
    pdf_path = FIXTURES_DIR / "mixed_report_part1_text_diagrams_keyvalue_comparison_timeseries.pdf"
    if not pdf_path.exists():
        pytest.skip("Fixture not yet generated")

    tables = extract_tables(str(pdf_path), classify=True)
    assert len(tables) == 3, f"Expected 3 tables from mixed report part 1, got {len(tables)}"


def test_extract_mixed_diagram_part2(ensure_fixtures):
    pdf_path = (
        FIXTURES_DIR / "mixed_report_part2_text_diagrams_hierarchical_matrix_relational_pivot.pdf"
    )
    if not pdf_path.exists():
        pytest.skip("Fixture not yet generated")

    tables = extract_tables(str(pdf_path), classify=True)
    assert len(tables) >= 3, (
        f"Expected at least 3 tables from mixed report part 2, got {len(tables)}"
    )
