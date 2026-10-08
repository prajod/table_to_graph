import pytest

from table_to_graph.models import TableData
from table_to_graph.normalizers import (
    DataTypeNormalizer,
    MergedCellNormalizer,
    MultiPageStitcher,
    NormalizerPipeline,
    WhitespaceNormalizer,
)


@pytest.fixture
def dirty_table():
    return TableData(
        headers=[["  Name  ", "Age "]],
        rows=[
            ["Alice\nSmith", "30"],
            [None, "25"],  # Implicit merged cell for Alice
            ["Bob", "  "],
        ],
    )


def test_whitespace_normalizer(dirty_table):
    normalizer = WhitespaceNormalizer()
    clean = normalizer.normalize(dirty_table)

    assert clean.headers[0] == ["Name", "Age"]
    assert clean.rows[0][0] == "Alice Smith"
    assert clean.rows[2][1] == ""  # "  " gets stripped to ""


def test_merged_cell_normalizer(dirty_table):
    normalizer = MergedCellNormalizer()
    filled = normalizer.normalize(dirty_table)

    # None gets replaced by the row above
    assert filled.rows[1][0] == "Alice\nSmith"
    assert filled.rows[0][0] == "Alice\nSmith"  # original unchanged


def test_data_type_normalizer():
    table = TableData(
        headers=[["A", "B", "C"]], rows=[["123", "2024-01-01", "Text"], ["", None, "45.6%"]]
    )
    normalizer = DataTypeNormalizer()
    typed = normalizer.normalize(table)

    meta = typed.cell_metadata
    assert meta is not None
    assert meta[0][0].data_type == "numeric"
    assert meta[0][1].data_type == "date"
    assert meta[0][2].data_type == "text"
    assert meta[1][0].data_type == "empty"
    assert meta[1][1].data_type == "empty"
    assert meta[1][2].data_type == "numeric"


def test_multipage_stitcher():
    t1 = TableData(headers=[["A", "B"]], rows=[[1, 2]])
    t1.metadata.page_number = 1
    t2 = TableData(headers=[["A", "B"]], rows=[[3, 4]])
    t2.metadata.page_number = 2
    t3 = TableData(headers=[["C", "D"]], rows=[[5, 6]])
    t3.metadata.page_number = 3

    stitcher = MultiPageStitcher()
    stitched = stitcher.stitch([t1, t2, t3])

    assert len(stitched) == 2
    # First table has merged rows
    assert stitched[0].rows == [[1, 2], [3, 4]]
    # Second table is separate due to different headers
    assert stitched[1].headers == [["C", "D"]]


def test_normalizer_pipeline(dirty_table):
    pipeline = NormalizerPipeline([WhitespaceNormalizer(), MergedCellNormalizer()])
    result = pipeline.normalize(dirty_table)

    # Both transformations applied
    assert result.headers[0] == ["Name", "Age"]
    assert result.rows[1][0] == "Alice Smith"  # Forward filled AND whitespace stripped
