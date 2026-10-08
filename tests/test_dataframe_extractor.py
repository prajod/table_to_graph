import pandas as pd
import pytest

from table_to_graph.extractors.dataframe_extractor import DataFrameExtractor


@pytest.fixture
def extractor():
    return DataFrameExtractor()


def test_can_handle(extractor):
    assert extractor.can_handle(pd.DataFrame())
    assert extractor.can_handle("data.csv")
    assert extractor.can_handle("data.tsv")
    assert extractor.can_handle("| Name | Age |\n|---|---|")
    assert extractor.can_handle("<table><tr><td>Hi</td></tr></table>")
    assert extractor.can_handle([["A", "B"], ["1", "2"]])
    assert not extractor.can_handle("plain text")


def test_extract_from_dataframe(extractor):
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    tables = extractor.extract(df)
    assert len(tables) == 1
    table = tables[0]
    assert table.headers == [["A", "B"]]
    assert table.rows == [[1, 3], [2, 4]]
    assert table.metadata.extraction_method == "dataframe"


def test_extract_from_markdown(extractor):
    md = """
    | Name | Age |
    |---|---|
    | Alice | 30 |
    | Bob | 25 |
    """
    tables = extractor.extract(md)
    assert len(tables) == 1
    assert tables[0].headers == [["Name", "Age"]]
    assert tables[0].rows == [["Alice", "30"], ["Bob", "25"]]


def test_extract_from_html(extractor):
    html = """
    <table>
      <tr><th>A</th><th>B</th></tr>
      <tr><td>1</td><td>2</td></tr>
    </table>
    """
    tables = extractor.extract(html)
    assert len(tables) == 1
    # HTML parsing may preserve string or numeric cell representations depending on parser backend
    assert tables[0].rows in ([["1", "2"]], [[1, 2]])


def test_extract_from_nested_list(extractor):
    data = [["Col1", "Col2"], ["Val1", "Val2"]]
    tables = extractor.extract(data)
    assert len(tables) == 1
    assert tables[0].headers == [["Col1", "Col2"]]
    assert tables[0].rows == [["Val1", "Val2"]]


def test_unsupported_source(extractor):
    with pytest.raises(ValueError, match="Unsupported source format"):
        extractor.extract("plain text string without markdown or html")
