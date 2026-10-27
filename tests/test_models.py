import pandas as pd

from table_to_graph.models import CellMeta, TableData, TableMetadata


def test_cell_meta_defaults():
    cell = CellMeta()
    assert cell.value is None
    assert cell.row_span == 1
    assert cell.col_span == 1
    assert cell.is_header is False
    assert cell.data_type == "text"


def test_table_metadata_source_tracking():
    meta = TableMetadata(source_file="doc.pdf", page_number=2, bbox=(0, 0, 10, 10))
    assert meta.source_file == "doc.pdf"
    assert meta.page_number == 2
    assert meta.bbox == (0, 0, 10, 10)


def test_table_data_construction(sample_table_data):
    assert len(sample_table_data.headers) == 1
    assert len(sample_table_data.rows) == 3
    assert sample_table_data.metadata.source_file == "test.pdf"


def test_table_data_to_dataframe(sample_table_data):
    df = sample_table_data.to_dataframe()
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["Name", "Age", "City"]
    assert len(df) == 3
    assert df.iloc[2]["Age"] is None


def test_table_data_from_dataframe():
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    table = TableData.from_dataframe(df)
    assert table.headers == [["A", "B"]]
    assert table.rows == [[1, 3], [2, 4]]
    assert table.metadata.extraction_method == "dataframe"


def test_table_data_multi_level_headers():
    df = pd.DataFrame({("Metric", "Sales"): [100], ("Metric", "Cost"): [50]})
    table = TableData.from_dataframe(df)
    assert len(table.headers) == 2
    assert table.headers[0] == ["Metric", "Metric"]
    assert table.headers[1] == ["Sales", "Cost"]

    # Check roundtrip
    df_out = table.to_dataframe()
    assert isinstance(df_out.columns, pd.MultiIndex)


def test_table_data_empty_detection():
    assert TableData(headers=[], rows=[]).is_empty is True
    assert TableData(headers=[["A"]], rows=[]).is_empty is False
    assert TableData(headers=[], rows=[["1"]]).is_empty is False


def test_table_data_dimensions(sample_table_data):
    assert sample_table_data.num_rows == 3
    assert sample_table_data.num_cols == 3


def test_table_data_none_cells(sample_table_data):
    assert sample_table_data.rows[2][1] is None
