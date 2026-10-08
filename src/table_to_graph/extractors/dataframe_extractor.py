import io
from pathlib import Path
from typing import Any

import pandas as pd

from table_to_graph.extractors import extractor_registry
from table_to_graph.models import TableData, TableMetadata


@extractor_registry.decorator("dataframe")
class DataFrameExtractor:
    """Extractor for non-PDF inputs like DataFrame, CSV, Markdown, and HTML tables.
    Conforms to the TableExtractor Protocol.
    """

    def can_handle(self, source: Any) -> bool:
        if isinstance(source, pd.DataFrame):
            return True
        if isinstance(source, (str, Path)) and str(source).lower().endswith((".csv", ".tsv")):
            return True
        if isinstance(source, str):
            # Check for markdown table (simple heuristic: contains |---|)
            if "|---" in source or "| ---" in source:
                return True
            # Check for HTML table
            if "<table" in source.lower():
                return True
        return bool(isinstance(source, list) and all(isinstance(row, list) for row in source))

    def extract(self, source: Any) -> list[TableData]:
        if not self.can_handle(source):
            raise ValueError("Unsupported source format for DataFrameExtractor")

        if isinstance(source, pd.DataFrame):
            return [self._from_dataframe(source)]

        if isinstance(source, (str, Path)):
            source_str = str(source).lower()
            if source_str.endswith(".csv"):
                df = pd.read_csv(source)
                return [self._from_dataframe(df, source_name=str(source))]
            elif source_str.endswith(".tsv"):
                df = pd.read_csv(source, sep="\t")
                return [self._from_dataframe(df, source_name=str(source))]

        if isinstance(source, str):
            if "|---" in source or "| ---" in source:
                return self._from_markdown(source)
            if "<table" in source.lower():
                return self._from_html(source)

        if isinstance(source, list):
            return [self._from_nested_list(source)]

        return []

    def _from_dataframe(self, df: pd.DataFrame, source_name: str = "dataframe") -> TableData:
        metadata = TableMetadata(source_file=source_name, extraction_method="dataframe")
        return TableData.from_dataframe(df, metadata=metadata)

    def _from_markdown(self, md_text: str) -> list[TableData]:
        # A very simplistic markdown parser. For production, a robust library might be better.
        tables = []
        lines = md_text.strip().split("\n")

        current_table = []
        for line in lines:
            if "|" in line:
                # Basic split and strip
                row = [cell.strip() for cell in line.split("|")][
                    1:-1
                ]  # Ignore first and last empty split if starting/ending with |
                # Skip separator lines
                if all(all(c in "-:" for c in cell.strip()) for cell in row if cell.strip()):
                    continue
                if row:
                    current_table.append(row)
            else:
                if current_table:
                    tables.append(self._from_nested_list(current_table, source_name="markdown"))
                    current_table = []

        if current_table:
            tables.append(self._from_nested_list(current_table, source_name="markdown"))

        return tables

    def _from_html(self, html_text: str) -> list[TableData]:
        try:
            dfs = pd.read_html(io.StringIO(html_text), flavor="bs4")
            return [self._from_dataframe(df, source_name="html") for df in dfs]
        except Exception:  # noqa: BLE001
            # Fallback simple BeautifulSoup parser if pd.read_html fails
            try:
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(html_text, "html.parser")
                tables = []
                for table in soup.find_all("table"):
                    data = []
                    for row in table.find_all("tr"):
                        cols = [ele.text.strip() for ele in row.find_all(["td", "th"])]
                        if cols:
                            data.append(cols)
                    if data:
                        tables.append(self._from_nested_list(data, source_name="html"))
                return tables
            except Exception:  # noqa: BLE001
                return []

    def _from_nested_list(
        self, data: list[list[str]], source_name: str = "nested_list"
    ) -> TableData:
        if not data:
            return TableData(headers=[], rows=[])

        headers = [data[0]]
        rows = data[1:]

        metadata = TableMetadata(source_file=source_name, extraction_method="dataframe")
        return TableData(headers=headers, rows=rows, metadata=metadata)
