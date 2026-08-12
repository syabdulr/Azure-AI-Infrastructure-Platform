"""A/B testing framework for multi-provider AI gateway."""

from .manager import ExperimentManager
from .models import (
    ABExperiment,
    ExperimentAssignment,
    ExperimentStatus,
    ExperimentVariant,
    VariantMetrics,
)

__all__ = [
    "ABExperiment",
    "ExperimentAssignment",
    "ExperimentStatus",
    "ExperimentVariant",
    "VariantMetrics",
    "ExperimentManager",
]
