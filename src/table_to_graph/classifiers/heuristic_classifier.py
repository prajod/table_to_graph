from collections.abc import Sequence

from table_to_graph.classifiers import classifier_registry
from table_to_graph.classifiers.features import extract_features
from table_to_graph.classifiers.rules import (
    ArchetypeRule,
    ComparisonRule,
    HierarchicalRule,
    KeyValueRule,
    MatrixRule,
    PivotRule,
    RelationalRule,
    TimeSeriesRule,
)
from table_to_graph.models import ClassificationResult, TableData


@classifier_registry.decorator("heuristic")
class HeuristicTableClassifier:
    """Rule-based classifier identifying table archetypes."""

    def __init__(
        self, rules: Sequence[ArchetypeRule] | None = None, fallback_threshold: float = 0.3
    ):
        if rules is None:
            self.rules: Sequence[ArchetypeRule] = [
                KeyValueRule(),
                ComparisonRule(),
                TimeSeriesRule(),
                HierarchicalRule(),
                MatrixRule(),
                RelationalRule(),
                PivotRule(),
            ]
        else:
            self.rules = rules

        self.fallback_threshold = fallback_threshold

    def classify(self, table: TableData) -> ClassificationResult:
        """Classify a table into its most likely structural archetype."""
        if table.is_empty:
            return ClassificationResult(
                table_type="unknown", confidence=0.0, metadata={"error": "Table is empty"}
            )

        features = extract_features(table)

        scores: dict[str, float] = {}
        for rule in self.rules:
            try:
                score = rule.evaluate(table, features)
                scores[rule.name] = score
            except Exception:  # noqa: BLE001
                scores[rule.name] = 0.0

        # Sort scores descending
        sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)

        if not sorted_scores:
            return ClassificationResult(table_type="unknown", confidence=0.0)

        primary_name, primary_score = sorted_scores[0]

        # Secondary candidates above threshold
        secondary_types = [
            name
            for name, score in sorted_scores[1:]
            if score >= self.fallback_threshold and score > 0.0
        ]

        # If the best score is 0, we really don't know
        if primary_score == 0.0:
            primary_name = "unknown"

        return ClassificationResult(
            table_type=primary_name,
            confidence=primary_score,
            secondary_types=secondary_types,
            metadata={
                "scores": scores,
                "features": {
                    "num_rows": features.num_rows,
                    "num_cols": features.num_cols,
                    "numeric_density": features.numeric_density,
                },
            },
        )
