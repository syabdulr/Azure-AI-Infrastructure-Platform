"""Scoring algorithms for prompt evaluation."""

import math
from collections import Counter
from typing import List

from .models import EvaluationMetric


class EvaluationScorer:
    """Scoring algorithms for comparing expected vs actual outputs."""

    def score_exact_match(self, expected: str, actual: str) -> float:
        """Score exact match (case-insensitive)."""
        return 1.0 if expected.strip().lower() == actual.strip().lower() else 0.0

    def score_contains_keywords(self, expected: str, actual: str, keywords: List[str]) -> float:
        """Score based on keyword containment."""
        if not keywords:
            return 0.0
        actual_lower = actual.lower()
        matches = sum(1 for kw in keywords if kw.lower() in actual_lower)
        return matches / len(keywords)

    def score_semantic_similarity(self, expected: str, actual: str) -> float:
        """
        Score semantic similarity using cosine similarity over TF-IDF vectors.
        Falls back to Jaccard similarity for short strings.
        """
        if not expected.strip() or not actual.strip():
            return 0.0

        # For short strings, use Jaccard similarity on word sets
        if len(expected.split()) < 5 or len(actual.split()) < 5:
            return self._jaccard_similarity(expected, actual)

        # For longer strings, use TF-IDF cosine similarity
        return self._cosine_similarity_tfidf(expected, actual)

    def score_length_ratio(self, expected: str, actual: str) -> float:
        """Score based on length ratio (penalizes too short or too long)."""
        exp_len = len(expected)
        act_len = len(actual)
        if exp_len == 0 and act_len == 0:
            return 1.0
        if exp_len == 0 or act_len == 0:
            return 0.0
        ratio = min(exp_len, act_len) / max(exp_len, act_len)
        return ratio

    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Compute Jaccard similarity between two strings."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 and not words2:
            return 1.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0.0

    def _cosine_similarity_tfidf(self, text1: str, text2: str) -> float:
        """Compute cosine similarity using TF-IDF vectors."""
        words1 = text1.lower().split()
        words2 = text2.lower().split()

        # Compute term frequencies
        tf1 = Counter(words1)
        tf2 = Counter(words2)

        # Get all unique terms
        all_terms = set(tf1.keys()).union(set(tf2.keys()))

        # Compute dot product and magnitudes
        dot_product = sum(tf1.get(t, 0) * tf2.get(t, 0) for t in all_terms)
        mag1 = math.sqrt(sum(v**2 for v in tf1.values()))
        mag2 = math.sqrt(sum(v**2 for v in tf2.values()))

        if mag1 == 0 or mag2 == 0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def compute_pass_threshold(
        self, scores: dict, metric: EvaluationMetric, threshold: float = 0.7
    ) -> bool:
        """Determine if a result passes based on metric and threshold."""
        metric_key = metric.value
        if metric_key not in scores:
            return False
        return bool(scores[metric_key] >= threshold)
