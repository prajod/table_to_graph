from typing import Protocol

from table_to_graph.classifiers.features import TableFeatures
from table_to_graph.models import TableData


class ArchetypeRule(Protocol):
    """Protocol for table archetype heuristic evaluators."""

    name: str

    def evaluate(self, table: TableData, features: TableFeatures) -> float:
        """Evaluate table features and return a confidence score [0.0, 1.0]."""
        ...


class KeyValueRule:
    name = "key_value"

    def evaluate(self, table: TableData, features: TableFeatures) -> float:
        if features.num_rows == 0 or features.num_cols == 0:
            return 0.0

        score = 0.0

        # 1. Structure (2-col or 3-col is ideal)
        if features.num_cols == 2:
            score += 0.4
        elif features.num_cols == 3:
            score += 0.2

        # 2. Labels (col0 ends with ':' or looks like a label)
        score += features.col0_label_ratio * 0.3

        # 3. Uniformity (if there are headers, they shouldn't be deep)
        if features.header_levels <= 1:
            score += 0.1

        # 4. Text/Mixed content (key-value rarely has dense numerics across all cols)
        if features.numeric_density < 0.8:
            score += 0.2

        return min(max(score, 0.0), 1.0)


class ComparisonRule:
    name = "comparison"

    def evaluate(self, table: TableData, features: TableFeatures) -> float:
        if features.num_rows < 2 or features.num_cols < 3:
            return 0.0

        score = 0.0

        # 1. Structure (many columns vs rows, or at least 3 cols)
        if features.num_cols >= 3:
            score += 0.3

        # 2. Header pattern (first col empty/label, others are entities)
        if features.header_strings and len(features.header_strings[0]) > 1:
            if features.header_strings[0][0].strip() == "":
                score += 0.2
            elif len(features.header_strings[0][0]) < 15:  # Short label like "Feature"
                score += 0.1

        # 3. Value similarity (if cols 1..N have similar data types)
        if len(features.col_types) > 1:
            rest_types = features.col_types[1:]
            if len(set(rest_types)) == 1:
                score += 0.4

        # 4. Multi-level headers usually imply Pivot/Hierarchical, not simple Comparison
        if features.header_levels > 1:
            score -= 0.3

        return min(max(score, 0.0), 1.0)


class TimeSeriesRule:
    name = "time_series"

    def evaluate(self, table: TableData, features: TableFeatures) -> float:
        if features.num_rows == 0 or features.num_cols < 2:
            return 0.0

        score = 0.0

        # 1. Temporal Headers
        if features.num_cols > 0:
            temporal_ratio = features.temporal_header_count / features.num_cols
            if temporal_ratio > 0.5:
                score += 0.6
            elif temporal_ratio > 0.2:
                score += 0.3

        # 2. Numeric Values (Time series body is usually numbers)
        if features.numeric_density > 0.5:
            score += 0.2

        # 3. Structure
        if features.header_levels == 1:
            score += 0.2

        return min(max(score, 0.0), 1.0)


class HierarchicalRule:
    name = "hierarchical"

    def evaluate(self, table: TableData, features: TableFeatures) -> float:
        if features.num_rows == 0 or features.num_cols == 0:
            return 0.0

        score = 0.0

        # 1. Header Depth (shared with pivot, moderate signal)
        if features.header_levels > 1:
            score += 0.4

        # 2. Nesting/Empty cells (hierarchical tables often have blank cells under merged parents)
        empty_col0 = any(h and h[0].strip() == "" for h in features.header_strings)
        if empty_col0:
            score += 0.2

        # 3. Indentation in Col0 — the DEFINITIVE hierarchical signal
        indent_count = sum(1 for d in features.col0_indent_depths if d > 0)
        indent_ratio = indent_count / features.num_rows if features.num_rows else 0.0
        if indent_ratio > 0.3:
            score += 0.7  # Very strong — indentation is unambiguous
        elif indent_ratio > 0.1:
            score += 0.5

        # 4. Numbered tree patterns in col0 (e.g. "1000 -", "1.1.1", "0 -")
        #    These survive PDF extraction even when indentation is lost
        import re

        tree_pattern = re.compile(r"^\s*\d+[\.\-]")
        tree_count = 0
        for row in table.rows:
            if row and row[0] is not None and tree_pattern.match(str(row[0])):
                tree_count += 1
        if features.num_rows > 0 and tree_count / features.num_rows > 0.5:
            score += 0.3

        # 5. If it's heavily multi-level (3+), it's likely a pivot, not simple hierarchical
        if features.header_levels >= 3:
            score -= 0.3

        return min(max(score, 0.0), 1.0)


class MatrixRule:
    name = "matrix"

    def evaluate(self, table: TableData, features: TableFeatures) -> float:
        if features.num_rows < 2 or features.num_cols < 2:
            return 0.0

        score = 0.0

        # 1. Symmetry
        if features.is_square:
            score += 0.4

        # 2. Header Overlap
        if features.row_col_header_overlap > 0.5:
            score += 0.3
        elif features.row_col_header_overlap > 0.2:
            score += 0.1

        # 3. Numeric Density
        if features.numeric_density > 0.7:
            score += 0.3

        return min(max(score, 0.0), 1.0)


class RelationalRule:
    name = "relational"

    def evaluate(self, table: TableData, features: TableFeatures) -> float:
        if features.num_rows == 0 or features.num_cols == 0:
            return 0.0

        score = 0.0

        # 1. FK Columns
        if features.fk_column_indices:
            score += 0.4

        # 2. Uniqueness (ID columns should be highly unique)
        high_unique = sum(1 for u in features.col_uniqueness if u > 0.9)
        if high_unique > 0:
            score += 0.3

        # 3. Standard Shape (many rows, few cols)
        if features.row_col_ratio > 2.0:
            score += 0.3

        return min(max(score, 0.0), 1.0)


class PivotRule:
    name = "pivot"

    def evaluate(self, table: TableData, features: TableFeatures) -> float:
        if features.num_rows == 0 or features.num_cols < 3:
            return 0.0

        score = 0.0

        # 1. Multi-level headers & horizontal span
        if features.header_levels > 1:
            score += 0.3
            if features.header_levels >= 3:
                score += 0.3  # Strong signal for Option A pivots
            if features.num_cols >= 4:
                score += 0.2

        # 2. Top-left is often blank or specifies "From/To"
        empty_or_from = any(
            h and h[0].strip().lower() in ("", "from") for h in features.header_strings
        )
        if empty_or_from:
            score += 0.2

        # 3. Aggregation (Body is mostly numeric)
        if features.numeric_density > 0.6:
            score += 0.2

        # 4. Check for repeating column headers in level 0
        if features.header_strings and len(features.header_strings[0]) > 2:
            unique_h0 = len(set(features.header_strings[0]))
            if unique_h0 < len(features.header_strings[0]):
                score += 0.2  # Repeated spanning headers

        return min(max(score, 0.0), 1.0)
