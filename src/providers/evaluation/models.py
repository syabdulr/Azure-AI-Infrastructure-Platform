"""Models for prompt evaluation pipeline with golden sets."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class MatchStrategy(Enum):
    """Strategy for matching expected vs actual output."""

    EXACT = "exact"
    CONTAINS = "contains"
    SEMANTIC = "semantic"


class EvaluationMetric(Enum):
    """Metrics for evaluating prompt outputs."""

    EXACT_MATCH = "exact_match"
    CONTAINS_KEYWORDS = "contains_keywords"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    LENGTH_RATIO = "length_ratio"


@dataclass
class GoldenTestCase:
    """A single golden test case with expected output."""

    test_id: str
    prompt: str
    expected_output: str
    context: Optional[str] = None
    category: str = "general"
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "prompt": self.prompt,
            "expected_output": self.expected_output,
            "context": self.context,
            "category": self.category,
            "tags": self.tags,
        }


@dataclass
class GoldenTestSet:
    """A collection of golden test cases."""

    name: str
    description: str = ""
    cases: List[GoldenTestCase] = field(default_factory=list)

    @property
    def size(self) -> int:
        return len(self.cases)

    def add_case(self, case: GoldenTestCase) -> None:
        self.cases.append(case)

    def remove_case(self, test_id: str) -> None:
        self.cases = [c for c in self.cases if c.test_id != test_id]

    def get_categories(self) -> List[str]:
        return list(set(c.category for c in self.cases))

    def filter_by_category(self, category: str) -> List[GoldenTestCase]:
        return [c for c in self.cases if c.category == category]

    def filter_by_tag(self, tag: str) -> List[GoldenTestCase]:
        return [c for c in self.cases if tag in c.tags]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "size": self.size,
            "categories": self.get_categories(),
            "cases": [c.to_dict() for c in self.cases],
        }


@dataclass
class EvaluationResult:
    """Result of evaluating a single test case."""

    test_id: str
    prompt: str
    expected_output: str
    actual_output: str
    scores: Dict[str, float] = field(default_factory=dict)
    latency_ms: float = 0.0
    error: Optional[str] = None
    passed: bool = False

    def __post_init__(self) -> None:
        """Auto-determine passed status based on scores if not explicitly set."""
        if not self.error and self.scores:
            self.passed = any(v >= 0.7 for v in self.scores.values())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "prompt": self.prompt,
            "expected_output": self.expected_output,
            "actual_output": self.actual_output,
            "scores": self.scores,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "passed": self.passed,
        }


@dataclass
class EvaluationReport:
    """Report from evaluating a golden test set against a provider."""

    test_set_name: str
    total_cases: int = 0
    passed_count: int = 0
    failed_count: int = 0
    error_count: int = 0
    results: List[EvaluationResult] = field(default_factory=list)
    category_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    avg_latency_ms: float = 0.0
    avg_scores: Dict[str, float] = field(default_factory=dict)
    metrics_used: List[str] = field(default_factory=list)

    @property
    def overall_pass_rate(self) -> float:
        if self.total_cases == 0:
            return 0.0
        return self.passed_count / self.total_cases

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_set_name": self.test_set_name,
            "total_cases": self.total_cases,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "error_count": self.error_count,
            "overall_pass_rate": self.overall_pass_rate,
            "results": [r.to_dict() for r in self.results],
            "category_breakdown": self.category_breakdown,
            "generated_at": self.generated_at,
            "avg_latency_ms": self.avg_latency_ms,
            "avg_scores": self.avg_scores,
            "metrics_used": self.metrics_used,
        }
