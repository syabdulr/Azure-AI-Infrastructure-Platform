"""Tests for A/B testing framework."""

from unittest.mock import MagicMock

import pytest

from src.providers.ab_testing.manager import ExperimentManager
from src.providers.ab_testing.models import (
    ABExperiment,
    ExperimentAssignment,
    ExperimentStatus,
    ExperimentVariant,
    VariantMetrics,
)


class TestExperimentVariant:
    """Test experiment variant model."""

    def test_variant_creation(self):
        """Test creating a variant."""
        variant = ExperimentVariant(
            name="control",
            provider="azure_openai",
            model="gpt-4",
            traffic_weight=50,
        )
        assert variant.name == "control"
        assert variant.provider == "azure_openai"
        assert variant.model == "gpt-4"
        assert variant.traffic_weight == 50

    def test_variant_with_description(self):
        """Test variant with description."""
        variant = ExperimentVariant(
            name="treatment",
            provider="openai",
            model="gpt-4-turbo",
            traffic_weight=50,
            description="Newer model version",
        )
        assert variant.description == "Newer model version"

    def test_variant_default_is_control(self):
        """Test variant is_control defaults to False."""
        variant = ExperimentVariant(
            name="treatment",
            provider="openai",
            model="gpt-4",
            traffic_weight=50,
        )
        assert variant.is_control is False


class TestABExperiment:
    """Test A/B experiment model."""

    @pytest.fixture
    def sample_variants(self):
        return [
            ExperimentVariant(
                name="control",
                provider="azure_openai",
                model="gpt-4",
                traffic_weight=50,
                is_control=True,
            ),
            ExperimentVariant(
                name="treatment",
                provider="openai",
                model="gpt-4-turbo",
                traffic_weight=50,
            ),
        ]

    def test_experiment_creation(self, sample_variants):
        """Test creating an experiment."""
        exp = ABExperiment(
            name="gpt4_turbo_test",
            description="Compare GPT-4 vs GPT-4-Turbo",
            variants=sample_variants,
        )
        assert exp.name == "gpt4_turbo_test"
        assert len(exp.variants) == 2
        assert exp.status == ExperimentStatus.DRAFT

    def test_experiment_total_traffic_weight(self, sample_variants):
        """Test total traffic weight calculation."""
        exp = ABExperiment(
            name="test",
            description="test",
            variants=sample_variants,
        )
        assert exp.total_traffic_weight() == 100

    def test_experiment_get_variant(self, sample_variants):
        """Test getting a variant by name."""
        exp = ABExperiment(
            name="test",
            description="test",
            variants=sample_variants,
        )
        control = exp.get_variant("control")
        assert control is not None
        assert control.is_control is True

        missing = exp.get_variant("nonexistent")
        assert missing is None

    def test_experiment_get_control(self, sample_variants):
        """Test getting the control variant."""
        exp = ABExperiment(
            name="test",
            description="test",
            variants=sample_variants,
        )
        control = exp.get_control_variant()
        assert control is not None
        assert control.name == "control"

    def test_experiment_validate_traffic_weights(self, sample_variants):
        """Test that traffic weights must sum to 100."""
        exp = ABExperiment(
            name="test",
            description="test",
            variants=sample_variants,
        )
        assert exp.validate_traffic() is True

    def test_experiment_validate_traffic_weights_invalid(self, sample_variants):
        """Test that invalid traffic weights are rejected."""
        bad_variants = [
            ExperimentVariant(
                name="a",
                provider="p1",
                model="m1",
                traffic_weight=30,
            ),
            ExperimentVariant(
                name="b",
                provider="p2",
                model="m2",
                traffic_weight=40,
            ),
        ]
        exp = ABExperiment(
            name="test",
            description="test",
            variants=bad_variants,
        )
        assert exp.validate_traffic() is False

    def test_experiment_start(self, sample_variants):
        """Test starting an experiment."""
        exp = ABExperiment(
            name="test",
            description="test",
            variants=sample_variants,
        )
        exp.start()
        assert exp.status == ExperimentStatus.RUNNING

    def test_experiment_cannot_start_without_valid_traffic(self):
        """Test experiment cannot start with invalid traffic."""
        bad_variants = [
            ExperimentVariant(name="a", provider="p1", model="m1", traffic_weight=30),
            ExperimentVariant(name="b", provider="p2", model="m2", traffic_weight=40),
        ]
        exp = ABExperiment(name="test", description="test", variants=bad_variants)
        with pytest.raises(ValueError, match="Traffic weights must sum to 100"):
            exp.start()

    def test_experiment_pause_and_resume(self, sample_variants):
        """Test pausing and resuming an experiment."""
        exp = ABExperiment(name="test", description="test", variants=sample_variants)
        exp.start()
        exp.pause()
        assert exp.status == ExperimentStatus.PAUSED
        exp.resume()
        assert exp.status == ExperimentStatus.RUNNING

    def test_experiment_complete(self, sample_variants):
        """Test completing an experiment."""
        exp = ABExperiment(name="test", description="test", variants=sample_variants)
        exp.start()
        exp.complete()
        assert exp.status == ExperimentStatus.COMPLETED


class TestVariantMetrics:
    """Test per-variant metrics tracking."""

    def test_metrics_creation(self):
        """Test creating metrics."""
        metrics = VariantMetrics(variant_name="control")
        assert metrics.variant_name == "control"
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0

    def test_record_success(self):
        """Test recording a successful request."""
        metrics = VariantMetrics(variant_name="control")
        metrics.record_request(success=True, latency_ms=500.0, cost_usd=0.02, tokens=100)
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1
        assert metrics.failed_requests == 0
        assert metrics.total_cost == 0.02
        assert metrics.total_tokens == 100

    def test_record_failure(self):
        """Test recording a failed request."""
        metrics = VariantMetrics(variant_name="control")
        metrics.record_request(success=False, latency_ms=3000.0, cost_usd=0.0, tokens=0)
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 1

    def test_success_rate(self):
        """Test success rate calculation."""
        metrics = VariantMetrics(variant_name="control")
        metrics.record_request(success=True, latency_ms=500.0, cost_usd=0.01, tokens=50)
        metrics.record_request(success=True, latency_ms=600.0, cost_usd=0.01, tokens=50)
        metrics.record_request(success=False, latency_ms=2000.0, cost_usd=0.0, tokens=0)
        assert metrics.total_requests == 3
        assert metrics.success_rate == pytest.approx(2 / 3)

    def test_avg_latency(self):
        """Test average latency calculation."""
        metrics = VariantMetrics(variant_name="control")
        metrics.record_request(success=True, latency_ms=100.0, cost_usd=0.01, tokens=50)
        metrics.record_request(success=True, latency_ms=300.0, cost_usd=0.01, tokens=50)
        assert metrics.avg_latency_ms == pytest.approx(200.0)

    def test_avg_cost_per_request(self):
        """Test average cost per request."""
        metrics = VariantMetrics(variant_name="control")
        metrics.record_request(success=True, latency_ms=100.0, cost_usd=0.02, tokens=50)
        metrics.record_request(success=True, latency_ms=100.0, cost_usd=0.04, tokens=50)
        assert metrics.avg_cost_per_request == pytest.approx(0.03)

    def test_empty_metrics(self):
        """Test metrics with no requests."""
        metrics = VariantMetrics(variant_name="control")
        assert metrics.success_rate == 0.0
        assert metrics.avg_latency_ms == 0.0
        assert metrics.avg_cost_per_request == 0.0


class TestExperimentManager:
    """Test experiment lifecycle management."""

    @pytest.fixture
    def manager(self):
        return ExperimentManager()

    @pytest.fixture
    def sample_experiment(self):
        return ABExperiment(
            name="gpt4_test",
            description="GPT-4 comparison",
            variants=[
                ExperimentVariant(
                    name="control",
                    provider="azure_openai",
                    model="gpt-4",
                    traffic_weight=50,
                    is_control=True,
                ),
                ExperimentVariant(
                    name="treatment",
                    provider="openai",
                    model="gpt-4-turbo",
                    traffic_weight=50,
                ),
            ],
        )

    def test_manager_creation(self, manager):
        """Test creating a manager."""
        assert manager.list_experiments() == []

    def test_register_experiment(self, manager, sample_experiment):
        """Test registering an experiment."""
        manager.register(sample_experiment)
        assert len(manager.list_experiments()) == 1
        assert "gpt4_test" in manager.list_experiments()

    def test_register_duplicate_experiment(self, manager, sample_experiment):
        """Test registering a duplicate experiment raises error."""
        manager.register(sample_experiment)
        with pytest.raises(ValueError, match="already registered"):
            manager.register(sample_experiment)

    def test_unregister_experiment(self, manager, sample_experiment):
        """Test unregistering an experiment."""
        manager.register(sample_experiment)
        manager.unregister("gpt4_test")
        assert len(manager.list_experiments()) == 0

    def test_get_experiment(self, manager, sample_experiment):
        """Test getting an experiment by name."""
        manager.register(sample_experiment)
        exp = manager.get_experiment("gpt4_test")
        assert exp is not None
        assert exp.name == "gpt4_test"

    def test_get_nonexistent_experiment(self, manager):
        """Test getting a non-existent experiment."""
        assert manager.get_experiment("nonexistent") is None

    def test_assign_variant_deterministic(self, manager, sample_experiment):
        """Test that assignment is deterministic for same request ID."""
        sample_experiment.start()
        manager.register(sample_experiment)

        assignment1 = manager.assign("gpt4_test", "user_123")
        assignment2 = manager.assign("gpt4_test", "user_123")

        assert assignment1 is not None
        assert assignment2 is not None
        assert assignment1.variant_name == assignment2.variant_name

    def test_assign_to_non_running_experiment(self, manager, sample_experiment):
        """Test assignment fails for non-running experiment."""
        manager.register(sample_experiment)
        assignment = manager.assign("gpt4_test", "user_123")
        assert assignment is None

    def test_assign_records_assignment(self, manager, sample_experiment):
        """Test that assignment is tracked."""
        sample_experiment.start()
        manager.register(sample_experiment)

        assignment = manager.assign("gpt4_test", "user_123")
        assert assignment is not None
        assert assignment.experiment_name == "gpt4_test"
        assert assignment.variant_name in ["control", "treatment"]
        assert assignment.request_id == "user_123"

    def test_assign_traffic_split(self, manager):
        """Test that traffic splits roughly according to weights."""
        import random

        exp = ABExperiment(
            name="split_test",
            description="Traffic split test",
            variants=[
                ExperimentVariant(
                    name="a", provider="p1", model="m1", traffic_weight=70, is_control=True
                ),
                ExperimentVariant(name="b", provider="p2", model="m2", traffic_weight=30),
            ],
        )
        exp.start()
        manager.register(exp)

        variant_a_count = 0
        variant_b_count = 0
        for i in range(1000):
            assignment = manager.assign("split_test", f"user_{i}")
            if assignment.variant_name == "a":
                variant_a_count += 1
            else:
                variant_b_count += 1

        # Should be roughly 70/30 (±10% tolerance)
        assert 600 <= variant_a_count <= 800
        assert 200 <= variant_b_count <= 400

    def test_record_outcome(self, manager, sample_experiment):
        """Test recording an outcome for a variant."""
        sample_experiment.start()
        manager.register(sample_experiment)

        assignment = manager.assign("gpt4_test", "user_123")
        manager.record_outcome(
            experiment_name="gpt4_test",
            request_id="user_123",
            success=True,
            latency_ms=500.0,
            cost_usd=0.02,
            tokens=100,
        )

        metrics = manager.get_variant_metrics("gpt4_test", assignment.variant_name)
        assert metrics.total_requests == 1
        assert metrics.successful_requests == 1

    def test_get_experiment_metrics(self, manager, sample_experiment):
        """Test getting all metrics for an experiment."""
        sample_experiment.start()
        manager.register(sample_experiment)

        for i in range(10):
            assignment = manager.assign("gpt4_test", f"user_{i}")
            manager.record_outcome(
                experiment_name="gpt4_test",
                request_id=f"user_{i}",
                success=True,
                latency_ms=500.0,
                cost_usd=0.02,
                tokens=100,
            )

        all_metrics = manager.get_experiment_metrics("gpt4_test")
        assert len(all_metrics) == 2  # control + treatment
        total_requests = sum(m.total_requests for m in all_metrics.values())
        assert total_requests == 10

    def test_start_experiment_via_manager(self, manager, sample_experiment):
        """Test starting an experiment through the manager."""
        manager.register(sample_experiment)
        manager.start_experiment("gpt4_test")
        exp = manager.get_experiment("gpt4_test")
        assert exp.status == ExperimentStatus.RUNNING

    def test_complete_experiment_via_manager(self, manager, sample_experiment):
        """Test completing an experiment through the manager."""
        manager.register(sample_experiment)
        manager.start_experiment("gpt4_test")
        manager.complete_experiment("gpt4_test")
        exp = manager.get_experiment("gpt4_test")
        assert exp.status == ExperimentStatus.COMPLETED

    def test_get_results_summary(self, manager, sample_experiment):
        """Test getting a results summary comparing variants."""
        sample_experiment.start()
        manager.register(sample_experiment)

        # Assign and record outcomes
        for i in range(20):
            assignment = manager.assign("gpt4_test", f"user_{i}")
            manager.record_outcome(
                experiment_name="gpt4_test",
                request_id=f"user_{i}",
                success=True,
                latency_ms=400.0 if assignment.variant_name == "control" else 300.0,
                cost_usd=0.03 if assignment.variant_name == "control" else 0.02,
                tokens=100,
            )

        summary = manager.get_results("gpt4_test")
        assert "control" in summary
        assert "treatment" in summary
        assert summary["control"]["total_requests"] > 0
        assert summary["treatment"]["total_requests"] > 0
        assert "success_rate" in summary["control"]
        assert "avg_latency_ms" in summary["control"]
        assert "avg_cost_per_request" in summary["control"]
