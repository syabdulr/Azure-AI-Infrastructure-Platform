"""Experiment manager for A/B testing framework."""

import hashlib
from typing import Dict, List, Optional

from .models import (
    ABExperiment,
    ExperimentAssignment,
    ExperimentStatus,
    ExperimentVariant,
    VariantMetrics,
)


class ExperimentManager:
    """Manages experiment lifecycle and variant assignment."""

    def __init__(self) -> None:
        """Initialize experiment manager."""
        self._experiments: Dict[str, ABExperiment] = {}
        self._metrics: Dict[str, Dict[str, VariantMetrics]] = {}
        self._assignments: Dict[str, ExperimentAssignment] = {}

    def register(self, experiment: ABExperiment) -> None:
        """Register a new experiment."""
        if experiment.name in self._experiments:
            raise ValueError(f"Experiment '{experiment.name}' already registered")
        self._experiments[experiment.name] = experiment
        self._metrics[experiment.name] = {}
        for variant in experiment.variants:
            self._metrics[experiment.name][variant.name] = VariantMetrics(variant_name=variant.name)

    def unregister(self, name: str) -> None:
        """Unregister an experiment."""
        if name in self._experiments:
            del self._experiments[name]
        if name in self._metrics:
            del self._metrics[name]

    def get_experiment(self, name: str) -> Optional[ABExperiment]:
        """Get an experiment by name."""
        return self._experiments.get(name)

    def list_experiments(self) -> List[str]:
        """List all experiment names."""
        return list(self._experiments.keys())

    def start_experiment(self, name: str) -> None:
        """Start an experiment."""
        exp = self._experiments.get(name)
        if exp:
            exp.start()

    def pause_experiment(self, name: str) -> None:
        """Pause an experiment."""
        exp = self._experiments.get(name)
        if exp:
            exp.pause()

    def complete_experiment(self, name: str) -> None:
        """Complete an experiment."""
        exp = self._experiments.get(name)
        if exp:
            exp.complete()

    def assign(self, experiment_name: str, request_id: str) -> Optional[ExperimentAssignment]:
        """
        Assign a request to a variant using deterministic hashing.

        Same request_id always maps to the same variant.
        Assignment only works for running experiments.

        Args:
            experiment_name: Name of the experiment
            request_id: Unique identifier for the request

        Returns:
            ExperimentAssignment if assigned, None if experiment not running
        """
        exp = self._experiments.get(experiment_name)
        if exp is None or exp.status != ExperimentStatus.RUNNING:
            return None

        # Check for existing assignment (idempotency)
        key = f"{experiment_name}:{request_id}"
        if key in self._assignments:
            return self._assignments[key]

        # Deterministic assignment via hash
        hash_input = f"{experiment_name}:{request_id}".encode()
        hash_val = int(hashlib.md5(hash_input).hexdigest(), 16)
        bucket = hash_val % 100  # 0-99

        # Find variant based on traffic weights
        cumulative = 0
        chosen_variant: Optional[ExperimentVariant] = None
        for variant in exp.variants:
            cumulative += variant.traffic_weight
            if bucket < cumulative:
                chosen_variant = variant
                break

        if chosen_variant is None:
            chosen_variant = exp.variants[-1]  # Fallback

        assignment = ExperimentAssignment(
            experiment_name=experiment_name,
            variant_name=chosen_variant.name,
            request_id=request_id,
            provider=chosen_variant.provider,
            model=chosen_variant.model,
        )

        self._assignments[key] = assignment
        return assignment

    def record_outcome(
        self,
        experiment_name: str,
        request_id: str,
        success: bool,
        latency_ms: float,
        cost_usd: float,
        tokens: int,
    ) -> None:
        """Record the outcome of a request assigned to an experiment."""
        key = f"{experiment_name}:{request_id}"
        assignment = self._assignments.get(key)
        if assignment is None:
            return

        metrics = self._metrics.get(experiment_name, {}).get(assignment.variant_name)
        if metrics:
            metrics.record_request(
                success=success,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                tokens=tokens,
            )

    def get_variant_metrics(
        self, experiment_name: str, variant_name: str
    ) -> Optional[VariantMetrics]:
        """Get metrics for a specific variant."""
        return self._metrics.get(experiment_name, {}).get(variant_name)

    def get_experiment_metrics(self, experiment_name: str) -> Dict[str, VariantMetrics]:
        """Get all variant metrics for an experiment."""
        return self._metrics.get(experiment_name, {})

    def get_results(self, experiment_name: str) -> Dict[str, dict]:
        """Get a results summary for all variants in an experiment."""
        metrics = self._metrics.get(experiment_name, {})
        return {name: m.to_dict() for name, m in metrics.items()}
