from pathlib import Path

import pytest

from table_to_graph.extractors.pdfplumber_extractor import PdfPlumberExtractor

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def test_can_handle():
    extractor = PdfPlumberExtractor()
    assert extractor.can_handle(FIXTURE_DIR / "sample_simple.pdf")
    assert extractor.can_handle(str(FIXTURE_DIR / "sample_simple.pdf"))
    assert not extractor.can_handle(FIXTURE_DIR / "sample.csv")
    assert not extractor.can_handle("some_random_text")


def test_extract_simple_table():
    # Only run if fixtures are generated
    pdf_path = FIXTURE_DIR / "sample_simple.pdf"
    if not pdf_path.exists():
        pytest.skip("Fixtures not generated yet. Run create_fixtures.py")

    extractor = PdfPlumberExtractor()
    tables = extractor.extract(pdf_path)

    assert len(tables) == 1
    table = tables[0]

    # Expected headers and rows from create_fixtures.py
    assert table.headers[0] == ["Name", "Age", "City"]
    assert table.num_rows == 5
    assert table.metadata.page_number == 1
    assert table.metadata.extraction_method == "pdfplumber"


def test_extract_multipage_table():
    pdf_path = FIXTURE_DIR / "sample_multipage.pdf"
    if not pdf_path.exists():
        pytest.skip("Fixtures not generated yet")

    extractor = PdfPlumberExtractor()
    tables = extractor.extract(pdf_path)
    # Multi-page tables with matching headers are automatically stitched into a single TableData
    assert len(tables) == 1
    assert tables[0].headers[0] == ["Name", "Age", "City"]
    assert tables[0].metadata.page_number == 2  # Reflects the merged end-state page
    assert tables[0].num_rows == 6


def test_extract_no_tables():
    pdf_path = FIXTURE_DIR / "sample_no_tables.pdf"
    if not pdf_path.exists():
        pytest.skip("Fixtures not generated yet")

    extractor = PdfPlumberExtractor()
    tables = extractor.extract(pdf_path)

    assert len(tables) == 0


def test_extract_from_pages():
    pdf_path = FIXTURE_DIR / "sample_multipage.pdf"
    if not pdf_path.exists():
        pytest.skip("Fixtures not generated yet")

    extractor = PdfPlumberExtractor()
    # Extract only from page 2 (index 1)
    tables = extractor.extract_from_pages(pdf_path, [1])

    assert len(tables) == 1
    assert tables[0].metadata.page_number == 2
