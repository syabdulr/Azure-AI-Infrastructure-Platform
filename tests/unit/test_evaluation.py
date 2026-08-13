"""Tests for prompt evaluation pipeline with golden sets."""

from unittest.mock import MagicMock

import pytest

from src.providers.evaluation.models import (
    EvaluationMetric,
    EvaluationReport,
    EvaluationResult,
    GoldenTestCase,
    GoldenTestSet,
    MatchStrategy,
)
from src.providers.evaluation.pipeline import EvaluationPipeline
from src.providers.evaluation.scorer import EvaluationScorer


class TestGoldenTestCase:
    """Tests for GoldenTestCase model."""

    def test_case_creation(self):
        """Test basic golden test case creation."""
        case = GoldenTestCase(
            test_id="test_001",
            prompt="What is 2 + 2?",
            expected_output="4",
            category="math",
            tags=["arithmetic", "basic"],
        )
        assert case.test_id == "test_001"
        assert case.prompt == "What is 2 + 2?"
        assert case.expected_output == "4"
        assert case.category == "math"
        assert case.tags == ["arithmetic", "basic"]

    def test_case_with_context(self):
        """Test golden test case with grounding context."""
        case = GoldenTestCase(
            test_id="test_002",
            prompt="What is the company policy on remote work?",
            expected_output="Employees may work remotely up to 3 days per week.",
            context="Company Policy Doc: Remote work is allowed up to 3 days per week.",
            category="policy",
            tags=["hr", "grounded"],
        )
        assert case.context is not None
        assert "Remote work" in case.context

    def test_case_defaults(self):
        """Test default values for golden test case."""
        case = GoldenTestCase(
            test_id="test_003",
            prompt="Hello",
            expected_output="Hi there",
        )
        assert case.category == "general"
        assert case.tags == []
        assert case.context is None


class TestGoldenTestSet:
    """Tests for GoldenTestSet model."""

    def test_empty_set(self):
        """Test creating an empty test set."""
        ts = GoldenTestSet(name="basic_set", description="Basic tests")
        assert ts.name == "basic_set"
        assert len(ts.cases) == 0
        assert ts.size == 0

    def test_add_cases(self):
        """Test adding cases to a test set."""
        ts = GoldenTestSet(name="math_set", description="Math tests")
        c1 = GoldenTestCase(test_id="t1", prompt="1+1", expected_output="2")
        c2 = GoldenTestCase(test_id="t2", prompt="2+2", expected_output="4")
        ts.add_case(c1)
        ts.add_case(c2)
        assert ts.size == 2
        assert ts.cases[0].test_id == "t1"

    def test_remove_case(self):
        """Test removing a case from a test set."""
        ts = GoldenTestSet(name="test_set", description="Test")
        c1 = GoldenTestCase(test_id="t1", prompt="q1", expected_output="a1")
        ts.add_case(c1)
        ts.remove_case("t1")
        assert ts.size == 0

    def test_get_categories(self):
        """Test getting all categories in a test set."""
        ts = GoldenTestSet(name="mixed", description="Mixed tests")
        ts.add_case(GoldenTestCase(test_id="t1", prompt="q", expected_output="a", category="math"))
        ts.add_case(GoldenTestCase(test_id="t2", prompt="q", expected_output="a", category="math"))
        ts.add_case(
            GoldenTestCase(test_id="t3", prompt="q", expected_output="a", category="policy")
        )
        cats = ts.get_categories()
        assert "math" in cats
        assert "policy" in cats
        assert len(cats) == 2

    def test_filter_by_category(self):
        """Test filtering cases by category."""
        ts = GoldenTestSet(name="mixed", description="Test")
        ts.add_case(GoldenTestCase(test_id="t1", prompt="q", expected_output="a", category="math"))
        ts.add_case(
            GoldenTestCase(test_id="t2", prompt="q", expected_output="a", category="policy")
        )
        filtered = ts.filter_by_category("math")
        assert len(filtered) == 1
        assert filtered[0].test_id == "t1"

    def test_filter_by_tag(self):
        """Test filtering cases by tag."""
        ts = GoldenTestSet(name="tagged", description="Test")
        ts.add_case(GoldenTestCase(test_id="t1", prompt="q", expected_output="a", tags=["basic"]))
        ts.add_case(
            GoldenTestCase(test_id="t2", prompt="q", expected_output="a", tags=["advanced"])
        )
        filtered = ts.filter_by_tag("basic")
        assert len(filtered) == 1
        assert filtered[0].test_id == "t1"


class TestEvaluationResult:
    """Tests for EvaluationResult model."""

    def test_result_creation(self):
        """Test basic evaluation result creation."""
        result = EvaluationResult(
            test_id="test_001",
            prompt="What is 2+2?",
            expected_output="4",
            actual_output="4",
            scores={"exact_match": 1.0, "semantic_similarity": 0.95},
        )
        assert result.test_id == "test_001"
        assert result.passed is True

    def test_result_failed(self):
        """Test evaluation result that failed."""
        result = EvaluationResult(
            test_id="test_002",
            prompt="What is the capital of France?",
            expected_output="Paris",
            actual_output="London",
            scores={"exact_match": 0.0},
        )
        assert result.passed is False

    def test_result_with_scores(self):
        """Test evaluation result with multiple scores."""
        result = EvaluationResult(
            test_id="test_003",
            prompt="Explain RAG",
            expected_output="RAG combines retrieval and generation...",
            actual_output="RAG is a technique that retrieves documents...",
            scores={
                "exact_match": 0.0,
                "contains_keywords": 1.0,
                "semantic_similarity": 0.82,
                "length_ratio": 0.75,
            },
        )
        assert result.scores["semantic_similarity"] == 0.82
        assert result.scores["contains_keywords"] == 1.0

    def test_result_with_latency(self):
        """Test evaluation result with latency tracking."""
        result = EvaluationResult(
            test_id="test_004",
            prompt="Hello",
            expected_output="Hi",
            actual_output="Hi",
            scores={"exact_match": 1.0},
            latency_ms=450.0,
        )
        assert result.latency_ms == 450.0

    def test_result_with_error(self):
        """Test evaluation result with an error."""
        result = EvaluationResult(
            test_id="test_005",
            prompt="Hello",
            expected_output="Hi",
            actual_output="",
            scores={},
            error="API timeout",
        )
        assert result.passed is False
        assert result.error == "API timeout"


class TestEvaluationScorer:
    """Tests for the evaluation scorer."""

    def test_exact_match(self):
        """Test exact match scoring."""
        scorer = EvaluationScorer()
        score = scorer.score_exact_match("Paris", "Paris")
        assert score == 1.0

    def test_exact_match_case_insensitive(self):
        """Test exact match with different case."""
        scorer = EvaluationScorer()
        score = scorer.score_exact_match("paris", "Paris")
        assert score == 1.0

    def test_exact_match_no_match(self):
        """Test exact match with no match."""
        scorer = EvaluationScorer()
        score = scorer.score_exact_match("Paris", "London")
        assert score == 0.0

    def test_contains_keywords(self):
        """Test keyword containment scoring."""
        scorer = EvaluationScorer()
        score = scorer.score_contains_keywords(
            expected="The policy allows remote work up to 3 days",
            actual="Employees can work remotely up to 3 days per week",
            keywords=["remote", "3 days"],
        )
        assert score == 1.0

    def test_contains_keywords_partial(self):
        """Test partial keyword match."""
        scorer = EvaluationScorer()
        score = scorer.score_contains_keywords(
            expected="The policy",
            actual="Employees can work remotely up to 3 days",
            keywords=["remote", "vacation"],
        )
        assert score == 0.5

    def test_contains_keywords_no_match(self):
        """Test keyword scoring with no matches."""
        scorer = ExtractionScorer = EvaluationScorer()
        score = scorer.score_contains_keywords(
            expected="The policy",
            actual="No relevant content here",
            keywords=["remote", "policy"],
        )
        assert score == 0.0

    def test_semantic_similarity_identical(self):
        """Test semantic similarity with identical strings."""
        scorer = EvaluationScorer()
        score = scorer.score_semantic_similarity("RAG", "RAG")
        assert score == 1.0

    def test_semantic_similarity_different(self):
        """Test semantic similarity with different strings."""
        scorer = EvaluationScorer()
        score = scorer.score_semantic_similarity(
            "RAG combines retrieval and generation", "Apples are red fruit"
        )
        assert score < 0.5

    def test_semantic_similarity_related(self):
        """Test semantic similarity with related content."""
        scorer = EvaluationScorer()
        score = scorer.score_semantic_similarity(
            "RAG retrieves documents to ground LLM responses",
            "RAG fetches relevant docs before generating answers",
        )
        assert score > 0.1  # Related content should have positive similarity

    def test_length_ratio(self):
        """Test length ratio scoring."""
        scorer = EvaluationScorer()
        score = scorer.score_length_ratio("short", "short")
        assert score == 1.0

    def test_length_ratio_different_lengths(self):
        """Test length ratio with very different lengths."""
        scorer = EvaluationScorer()
        score = scorer.score_length_ratio("short", "this is a much longer response than expected")
        assert score < 0.5

    def test_length_ratio_actual_longer(self):
        """Test length ratio when actual is longer."""
        scorer = EvaluationScorer()
        score = scorer.score_length_ratio(
            "this is a much longer response",
            "short",
        )
        assert score < 0.5


class TestEvaluationPipeline:
    """Tests for the evaluation pipeline."""

    def _make_simple_set(self):
        """Create a simple golden test set for testing."""
        ts = GoldenTestSet(name="basic", description="Basic tests")
        ts.add_case(
            GoldenTestCase(
                test_id="t1",
                prompt="What is 2+2?",
                expected_output="4",
                category="math",
            )
        )
        ts.add_case(
            GoldenTestCase(
                test_id="t2",
                prompt="What is the capital of France?",
                expected_output="Paris",
                category="geography",
            )
        )
        return ts

    def test_pipeline_creation(self):
        """Test creating an evaluation pipeline."""
        scorer = EvaluationScorer()
        pipeline = EvaluationPipeline(scorer=scorer)
        assert pipeline is not None

    def test_pipeline_evaluate_exact_match(self):
        """Test pipeline evaluating with exact match strategy."""
        scorer = EvaluationScorer()
        pipeline = EvaluationPipeline(scorer=scorer)

        ts = self._make_simple_set()

        # Provider returns exact matches
        def provider_fn(prompt: str) -> str:
            if "2+2" in prompt:
                return "4"
            return "Paris"

        report = pipeline.evaluate(
            test_set=ts,
            provider_fn=provider_fn,
            metrics=[EvaluationMetric.EXACT_MATCH],
        )
        assert report.total_cases == 2
        assert report.passed_count == 2
        assert report.overall_pass_rate == 1.0

    def test_pipeline_evaluate_with_failures(self):
        """Test pipeline evaluating with some failures."""
        scorer = EvaluationScorer()
        pipeline = EvaluationPipeline(scorer=scorer)

        ts = self._make_simple_set()

        def provider_fn(prompt: str) -> str:
            if "2+2" in prompt:
                return "5"  # Wrong answer
            return "Paris"

        report = pipeline.evaluate(
            test_set=ts,
            provider_fn=provider_fn,
            metrics=[EvaluationMetric.EXACT_MATCH],
        )
        assert report.total_cases == 2
        assert report.passed_count == 1
        assert report.overall_pass_rate == 0.5

    def test_pipeline_evaluate_with_error(self):
        """Test pipeline evaluating with API error."""
        scorer = EvaluationScorer()
        pipeline = EvaluationPipeline(scorer=scorer)

        ts = self._make_simple_set()

        def provider_fn(prompt: str) -> str:
            raise RuntimeError("API timeout")

        report = pipeline.evaluate(
            test_set=ts,
            provider_fn=provider_fn,
            metrics=[EvaluationMetric.EXACT_MATCH],
        )
        assert report.total_cases == 2
        assert report.error_count == 2
        assert report.passed_count == 0

    def test_pipeline_evaluate_semantic(self):
        """Test pipeline evaluating with semantic similarity."""
        scorer = EvaluationScorer()
        pipeline = EvaluationPipeline(scorer=scorer)

        ts = GoldenTestSet(name="semantic", description="Semantic tests")
        ts.add_case(
            GoldenTestCase(
                test_id="t1",
                prompt="Explain what RAG is",
                expected_output="RAG combines retrieval of relevant documents with LLM generation",
                category="tech",
            )
        )

        def provider_fn(prompt: str) -> str:
            return "RAG fetches relevant docs and generates answers grounded in them"

        report = pipeline.evaluate(
            test_set=ts,
            provider_fn=provider_fn,
            metrics=[EvaluationMetric.SEMANTIC_SIMILARITY],
            threshold=0.15,
        )
        assert report.total_cases == 1
        assert report.passed_count == 1
        assert report.overall_pass_rate == 1.0

    def test_pipeline_category_breakdown(self):
        """Test pipeline generating category breakdown."""
        scorer = EvaluationScorer()
        pipeline = EvaluationPipeline(scorer=scorer)

        ts = self._make_simple_set()

        def provider_fn(prompt: str) -> str:
            return "wrong answer"

        report = pipeline.evaluate(
            test_set=ts,
            provider_fn=provider_fn,
            metrics=[EvaluationMetric.EXACT_MATCH],
        )
        assert "math" in report.category_breakdown
        assert "geography" in report.category_breakdown
        assert report.category_breakdown["math"]["pass_rate"] == 0.0
        assert report.category_breakdown["geography"]["pass_rate"] == 0.0

    def test_pipeline_with_latency_tracking(self):
        """Test pipeline tracking latency."""
        scorer = EvaluationScorer()
        pipeline = EvaluationPipeline(scorer=scorer)

        ts = self._make_simple_set()

        def provider_fn(prompt: str) -> str:
            return "4" if "2+2" in prompt else "Paris"

        report = pipeline.evaluate(
            test_set=ts,
            provider_fn=provider_fn,
            metrics=[EvaluationMetric.EXACT_MATCH],
        )
        assert report.avg_latency_ms > 0

    def test_pipeline_regression_detection(self):
        """Test pipeline comparing two runs for regression."""
        scorer = EvaluationScorer()
        pipeline = EvaluationPipeline(scorer=scorer)

        ts = self._make_simple_set()

        # Baseline run — all pass
        report_baseline = pipeline.evaluate(
            test_set=ts,
            provider_fn=lambda p: "4" if "2+2" in p else "Paris",
            metrics=[EvaluationMetric.EXACT_MATCH],
        )

        # New run — one regression
        report_new = pipeline.evaluate(
            test_set=ts,
            provider_fn=lambda p: "5" if "2+2" in p else "Paris",
            metrics=[EvaluationMetric.EXACT_MATCH],
        )

        regression = pipeline.detect_regression(report_baseline, report_new)
        assert regression["has_regression"] is True
        assert len(regression["regressed_cases"]) == 1
        assert regression["regressed_cases"][0] == "t1"

    def test_pipeline_export_results(self):
        """Test exporting evaluation results."""
        scorer = EvaluationScorer()
        pipeline = EvaluationPipeline(scorer=scorer)

        ts = self._make_simple_set()

        report = pipeline.evaluate(
            test_set=ts,
            provider_fn=lambda p: "4" if "2+2" in p else "Paris",
            metrics=[EvaluationMetric.EXACT_MATCH],
        )

        exported = report.to_dict()
        assert "total_cases" in exported
        assert "passed_count" in exported
        assert "overall_pass_rate" in exported
        assert "results" in exported
        assert exported["total_cases"] == 2
        assert exported["overall_pass_rate"] == 1.0
