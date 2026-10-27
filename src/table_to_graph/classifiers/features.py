"""Shared feature extraction for classification rules.

Features are computed once per table and reused by all 7 archetype evaluators.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from table_to_graph.models import TableData

# ── Temporal patterns ────────────────────────────────────────────────────────
_TEMPORAL_RE = re.compile(
    r"""
    (?:^|\b)
    (?:
        Q[1-4]                          # Q1 .. Q4
        | (?:Jan|Feb|Mar|Apr|May|Jun    # Month abbreviations
           |Jul|Aug|Sep|Oct|Nov|Dec)
        | (?:January|February|March|April|May|June
           |July|August|September|October|November|December)
        | \d{4}[-/]\d{1,2}             # YYYY-MM  or  YYYY/MM
        | \d{4}                         # bare year
        | FY\s?\d{2,4}                 # FY23, FY 2024
        | H[12]                         # H1, H2 (half-year)
        | CY\s?\d{2,4}                 # CY23
    )
    (?:\b|$)
    """,
    re.IGNORECASE | re.VERBOSE,
)

# ── FK-like column patterns ──────────────────────────────────────────────────
_FK_RE = re.compile(
    r"""
    (?:^|_)
    (?:id|key|ref|fk|pk|code)
    (?:$|_)
    """,
    re.IGNORECASE | re.VERBOSE,
)


@dataclass
class TableFeatures:
    """Pre-computed structural signals for a single table."""

    num_rows: int = 0
    num_cols: int = 0
    header_levels: int = 0

    # Per-column dominant data type ("text" | "numeric" | "date" | "empty")
    col_types: list[str] = field(default_factory=list)

    # Per-column ratio of unique non-empty values to total rows
    col_uniqueness: list[float] = field(default_factory=list)

    # Fraction of all body cells that look numeric
    numeric_density: float = 0.0

    # How many header strings match temporal patterns
    temporal_header_count: int = 0

    # Indices of columns whose header matches FK naming conventions
    fk_column_indices: list[int] = field(default_factory=list)

    # Per-row leading-whitespace count for column 0 (indentation signal)
    col0_indent_depths: list[int] = field(default_factory=list)

    # Flattened header strings (level 0, or all levels concatenated)
    header_strings: list[list[str]] = field(default_factory=list)

    # Derived ratios
    row_col_ratio: float = 0.0
    is_square: bool = False

    # Whether col0 values look like labels ending in ":"
    col0_label_ratio: float = 0.0

    # Overlap ratio between row-header values (col0) and column headers
    row_col_header_overlap: float = 0.0


# ── Numeric detection ────────────────────────────────────────────────────────
_NUMERIC_RE = re.compile(r"^-?[\d,]+(\.\d+)?%?$")


def _is_numeric(val: str | None) -> bool:
    if not val or not isinstance(val, str):
        return False
    return bool(_NUMERIC_RE.match(val.strip()))


def _is_temporal(val: str | None) -> bool:
    if not val or not isinstance(val, str):
        return False
    return bool(_TEMPORAL_RE.search(val.strip()))


def _leading_spaces(val: str | None) -> int:
    if not val or not isinstance(val, str):
        return 0
    return len(val) - len(val.lstrip())


# ── Main extractor ───────────────────────────────────────────────────────────


def extract_features(table: TableData) -> TableFeatures:
    """Single-pass feature extraction over a TableData instance."""

    feat = TableFeatures()

    # Basic dimensions
    feat.num_rows = table.num_rows
    feat.num_cols = table.num_cols
    feat.header_levels = len(table.headers)
    feat.header_strings = [list(h) for h in table.headers]

    if feat.num_cols == 0:
        return feat

    # Row / col ratio
    feat.row_col_ratio = feat.num_rows / feat.num_cols if feat.num_cols else 0.0
    ratio = feat.num_rows / feat.num_cols if feat.num_cols else 0.0
    feat.is_square = 0.7 <= ratio <= 1.3 and feat.num_rows >= 2

    # ── Per-column accumulators ──────────────────────────────────────────
    col_numeric_counts: list[int] = [0] * feat.num_cols
    col_date_counts: list[int] = [0] * feat.num_cols
    col_empty_counts: list[int] = [0] * feat.num_cols
    col_value_sets: list[set[str]] = [set() for _ in range(feat.num_cols)]
    total_cells = 0
    total_numeric = 0

    label_count = 0  # col0 values ending with ':'

    for row in table.rows:
        for c_idx in range(min(len(row), feat.num_cols)):
            cell = row[c_idx]
            cell_str = str(cell).strip() if cell is not None else ""
            total_cells += 1

            if not cell_str:
                col_empty_counts[c_idx] += 1
                continue

            col_value_sets[c_idx].add(cell_str)

            if _is_numeric(cell_str):
                col_numeric_counts[c_idx] += 1
                total_numeric += 1
            elif _is_temporal(cell_str):
                col_date_counts[c_idx] += 1

        # Col0 indent & label detection
        if row and len(row) > 0:
            c0 = row[0]
            feat.col0_indent_depths.append(_leading_spaces(str(c0) if c0 is not None else ""))
            c0_str = str(c0).strip() if c0 is not None else ""
            if c0_str.endswith(":"):
                label_count += 1

    # ── Derived per-column stats ─────────────────────────────────────────
    for c_idx in range(feat.num_cols):
        non_empty = feat.num_rows - col_empty_counts[c_idx]
        if non_empty == 0:
            feat.col_types.append("empty")
            feat.col_uniqueness.append(0.0)
            continue

        if col_numeric_counts[c_idx] / non_empty >= 0.6:
            feat.col_types.append("numeric")
        elif col_date_counts[c_idx] / non_empty >= 0.4:
            feat.col_types.append("date")
        else:
            feat.col_types.append("text")

        feat.col_uniqueness.append(len(col_value_sets[c_idx]) / non_empty if non_empty else 0.0)

    # Numeric density
    feat.numeric_density = total_numeric / total_cells if total_cells else 0.0

    # Col0 label ratio
    feat.col0_label_ratio = label_count / feat.num_rows if feat.num_rows else 0.0

    # ── Header-level signals ─────────────────────────────────────────────
    if feat.header_strings:
        flat_headers = feat.header_strings[0]
        for h in flat_headers:
            if _is_temporal(h):
                feat.temporal_header_count += 1
            if _FK_RE.search(h):
                feat.fk_column_indices.append(flat_headers.index(h))

    # Row-header / col-header overlap (for matrix detection)
    if feat.header_strings and feat.num_rows >= 2:
        col_header_set = {h.lower().strip() for h in feat.header_strings[0]}
        row_header_set = set()
        for row in table.rows:
            if row and row[0] is not None:
                row_header_set.add(str(row[0]).lower().strip())
        if col_header_set and row_header_set:
            intersection = col_header_set & row_header_set
            union = col_header_set | row_header_set
            feat.row_col_header_overlap = len(intersection) / len(union) if union else 0.0

    return feat
