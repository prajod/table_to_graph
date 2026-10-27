import re
from collections.abc import Sequence
from typing import Any

import pandas as pd

from table_to_graph.interfaces import Normalizer
from table_to_graph.models import CellMeta, PipelineConfig, TableData
from table_to_graph.registry import Registry

normalizer_registry = Registry[Normalizer]("normalizers")


@normalizer_registry.decorator("whitespace")
class WhitespaceNormalizer:
    """Strips leading/trailing whitespace and normalizes newlines."""

    def normalize(self, table: TableData) -> TableData:
        new_table = table.model_copy(deep=True)

        for r_idx, row in enumerate(new_table.rows):
            for c_idx, cell in enumerate(row):
                if isinstance(cell, str):
                    new_table.rows[r_idx][c_idx] = " ".join(cell.split())

        for r_idx, header_row in enumerate(new_table.headers):
            for c_idx, cell in enumerate(header_row):
                if isinstance(cell, str):
                    new_table.headers[r_idx][c_idx] = " ".join(cell.split())

        return new_table


@normalizer_registry.decorator("merged_cells")
class MergedCellNormalizer:
    """Forward-fills None cells from the row above (handles row-span)."""

    def normalize(self, table: TableData) -> TableData:
        new_table = table.model_copy(deep=True)

        for r_idx in range(1, len(new_table.rows)):
            for c_idx in range(len(new_table.rows[r_idx])):
                if new_table.rows[r_idx][c_idx] is None or new_table.rows[r_idx][c_idx] == "":
                    # Propagate from the cell above
                    new_table.rows[r_idx][c_idx] = new_table.rows[r_idx - 1][c_idx]

        return new_table


@normalizer_registry.decorator("data_types")
class DataTypeNormalizer:
    """Detects data types and populates cell_metadata."""

    def _detect_type(self, value: Any) -> str:
        if pd.isna(value) if isinstance(value, float) else value is None:
            return "empty"

        if isinstance(value, (int, float)):
            return "numeric"

        str_val = str(value).strip()
        if not str_val:
            return "empty"

        # Simple numeric check for strings
        if re.match(r"^-?[\d,]+(\.\d+)?%?$", str_val):
            return "numeric"

        # Simple date check (YYYY-MM-DD or MM/DD/YYYY)
        if re.match(r"^\d{4}-\d{2}-\d{2}$", str_val) or re.match(
            r"^\d{1,2}/\d{1,2}/\d{2,4}$", str_val
        ):
            return "date"

        return "text"

    def normalize(self, table: TableData) -> TableData:
        new_table = table.model_copy(deep=True)

        cell_meta_matrix = []
        for row in new_table.rows:
            meta_row = []
            for cell in row:
                d_type = self._detect_type(cell)
                meta_row.append(CellMeta(value=cell, data_type=d_type))  # type: ignore
            cell_meta_matrix.append(meta_row)

        new_table.cell_metadata = cell_meta_matrix
        return new_table


@normalizer_registry.decorator("multipage_stitch")
class MultiPageStitcher:
    """Merges consecutive tables with matching headers across pages.
    Note: This violates the 1-to-1 Normalizer protocol slightly if used per-table.
    Usually applied to a list of tables. We adapt it to process lists.
    """

    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold

    def normalize(self, table: TableData) -> TableData:
        """No-op for single table; MultiPageStitcher operates on table sequences."""
        return table

    def _jaccard_similarity(self, list1: list[str], list2: list[str]) -> float:
        set1 = {str(x).lower().strip() for x in list1}
        set2 = {str(x).lower().strip() for x in list2}
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union

    def stitch(self, tables: Sequence[TableData]) -> list[TableData]:
        if not tables:
            return []

        stitched = [tables[0].model_copy(deep=True)]

        for table in tables[1:]:
            prev_table = stitched[-1]

            # Check if headers match
            if prev_table.headers and table.headers:
                sim = self._jaccard_similarity(prev_table.headers[0], table.headers[0])
                if sim >= self.similarity_threshold:
                    # Merge rows
                    prev_table.rows.extend(table.rows)
                    # Extend metadata bounding box or indicate spanning
                    # In a real impl, we'd record a list of bboxes. For now, we just update the page_number if it's different.
                    if prev_table.metadata.page_number != table.metadata.page_number:
                        # Convert to a string indicating range, or leave as starting page.
                        pass
                    continue

            stitched.append(table.model_copy(deep=True))

        return stitched


class NormalizerPipeline:
    """Chains multiple normalizers together."""

    def __init__(self, normalizers: list[Normalizer]):
        self.normalizers = normalizers

    def normalize(self, table: TableData) -> TableData:
        current_table = table
        for normalizer in self.normalizers:
            current_table = normalizer.normalize(current_table)
        return current_table

    def normalize_all(
        self, tables: list[TableData], stitcher: MultiPageStitcher | None = None
    ) -> list[TableData]:
        # First stitch if configured
        if stitcher:
            tables = stitcher.stitch(tables)

        # Then normalize each
        return [self.normalize(t) for t in tables]

    @classmethod
    def from_config(cls, config: PipelineConfig) -> "NormalizerPipeline":
        instances = []
        for name in config.normalizer_chain:
            # We ignore multipage_stitch here as it's applied differently,
            # but if it's in the chain we can instantiate it for later use.
            if name != "multipage_stitch":
                instances.append(normalizer_registry.get(name)())
        return cls(instances)
