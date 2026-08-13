"""Evaluation pipeline for running golden test sets against providers."""

import time
from typing import Any, Callable, Dict, List, Optional

from .models import (
    EvaluationMetric,
    EvaluationReport,
    EvaluationResult,
    GoldenTestCase,
    GoldenTestSet,
)
from .scorer import EvaluationScorer


class EvaluationPipeline:
    """Pipeline for evaluating prompts against golden test sets."""

    def __init__(self, scorer: Optional[EvaluationScorer] = None) -> None:
        self.scorer = scorer or EvaluationScorer()

    def evaluate(
        self,
        test_set: GoldenTestSet,
        provider_fn: Callable[[str], str],
        metrics: List[EvaluationMetric],
        threshold: float = 0.7,
    ) -> EvaluationReport:
        """
        Evaluate a golden test set against a provider function.

        Args:
            test_set: The golden test set to evaluate.
            provider_fn: Function that takes a prompt and returns a response.
            metrics: List of metrics to compute.
            threshold: Minimum score threshold for passing.

        Returns:
            EvaluationReport with results.
        """
        report = EvaluationReport(
            test_set_name=test_set.name,
            metrics_used=[m.value for m in metrics],
        )

        latencies: List[float] = []
        metric_totals: Dict[str, List[float]] = {m.value: [] for m in metrics}

        for case in test_set.cases:
            result = self._evaluate_case(case, provider_fn, metrics, threshold)
            report.results.append(result)

            if result.error:
                report.error_count += 1
            elif result.passed:
                report.passed_count += 1
            else:
                report.failed_count += 1

            if result.latency_ms > 0:
                latencies.append(result.latency_ms)

            for metric_key, score in result.scores.items():
                if metric_key in metric_totals:
                    metric_totals[metric_key].append(score)

        report.total_cases = len(test_set.cases)
        report.avg_latency_ms = sum(latencies) / len(latencies) if latencies else 0.0
        report.avg_scores = {k: sum(v) / len(v) for k, v in metric_totals.items() if v}
        report.category_breakdown = self._compute_category_breakdown(test_set, report.results)

        return report

    def _evaluate_case(
        self,
        case: GoldenTestCase,
        provider_fn: Callable[[str], str],
        metrics: List[EvaluationMetric],
        threshold: float,
    ) -> EvaluationResult:
        """Evaluate a single golden test case."""
        result = EvaluationResult(
            test_id=case.test_id,
            prompt=case.prompt,
            expected_output=case.expected_output,
            actual_output="",
        )

        # Call provider
        try:
            start = time.time()
            actual = provider_fn(case.prompt)
            elapsed = (time.time() - start) * 1000
            result.actual_output = actual
            result.latency_ms = elapsed
        except Exception as e:
            result.error = str(e)
            return result

        # Compute scores
        passed = True
        for metric in metrics:
            score = self._compute_metric(metric, case.expected_output, actual)
            result.scores[metric.value] = score
            if score < threshold:
                passed = False

        result.passed = passed
        return result

    def _compute_metric(self, metric: EvaluationMetric, expected: str, actual: str) -> float:
        """Compute a single metric score."""
        if metric == EvaluationMetric.EXACT_MATCH:
            return self.scorer.score_exact_match(expected, actual)
        elif metric == EvaluationMetric.SEMANTIC_SIMILARITY:
            return self.scorer.score_semantic_similarity(expected, actual)
        elif metric == EvaluationMetric.LENGTH_RATIO:
            return self.scorer.score_length_ratio(expected, actual)
        elif metric == EvaluationMetric.CONTAINS_KEYWORDS:
            keywords = expected.split()[:5]  # Use first 5 words as keywords
            return self.scorer.score_contains_keywords(expected, actual, keywords)
        return 0.0

    def _compute_category_breakdown(
        self, test_set: GoldenTestSet, results: List[EvaluationResult]
    ) -> Dict[str, Dict[str, Any]]:
        """Compute per-category breakdown of results."""
        breakdown: Dict[str, Dict[str, Any]] = {}
        for category in test_set.get_categories():
            category_case_ids = {c.test_id for c in test_set.filter_by_category(category)}
            category_results = [r for r in results if r.test_id in category_case_ids]
            passed = sum(1 for r in category_results if r.passed)
            total = len(category_results)
            breakdown[category] = {
                "total": total,
                "passed": passed,
                "pass_rate": passed / total if total > 0 else 0.0,
            }
        return breakdown

    def detect_regression(
        self,
        baseline: EvaluationReport,
        current: EvaluationReport,
    ) -> Dict[str, Any]:
        """
        Detect regressions between two evaluation runs.

        Args:
            baseline: The baseline (previous) evaluation report.
            current: The current evaluation report.

        Returns:
            Dict with has_regression, regressed_cases, improved_cases.
        """
        baseline_results = {r.test_id: r for r in baseline.results}
        current_results = {r.test_id: r for r in current.results}

        regressed: List[str] = []
        improved: List[str] = []

        for test_id, current_result in current_results.items():
            if test_id not in baseline_results:
                continue
            baseline_result = baseline_results[test_id]
            if baseline_result.passed and not current_result.passed:
                regressed.append(test_id)
            elif not baseline_result.passed and current_result.passed:
                improved.append(test_id)

        return {
            "has_regression": len(regressed) > 0,
            "regressed_cases": regressed,
            "improved_cases": improved,
            "baseline_pass_rate": baseline.overall_pass_rate,
            "current_pass_rate": current.overall_pass_rate,
        }
