"""
Prompt evaluation framework for Azure AI Infrastructure Platform

This module provides:
- Quality metrics evaluation
- Relevance scoring
- Coherence metrics
- Completeness evaluation
- Overall scoring
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptEvaluator:
    """Evaluate prompt quality and effectiveness"""

    def __init__(self):
        """Initialize evaluator"""
        self.evaluators = {
            "quality": self._evaluate_quality,
            "relevance": self._evaluate_relevance,
            "coherence": self._evaluate_coherence,
            "completeness": self._evaluate_completeness,
        }

    def evaluate(
        self,
        prompt: str,
        response: str,
        expected_answer: Optional[str] = None,
        context: Optional[str] = None,
        query: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        Evaluate prompt performance

        Args:
            prompt: The prompt used
            response: The model's response
            expected_answer: Expected answer (for accuracy evaluation)
            context: Context provided to the model
            query: User query

        Returns:
            Dictionary with metrics (0-1 scale):
            - quality: Overall response quality
            - relevance: Relevance to query
            - coherence: Logical coherence
            - completeness: Information completeness
            - overall: Overall score
        """
        metrics = {}

        # Evaluate each metric
        for metric_name, evaluator in self.evaluators.items():
            try:
                score = evaluator(
                    prompt=prompt,
                    response=response,
                    expected_answer=expected_answer,
                    context=context,
                    query=query,
                )
                metrics[metric_name] = round(score, 4)
            except Exception as e:
                logger.error(f"Error evaluating {metric_name}: {e}")
                metrics[metric_name] = 0.0

        # Calculate overall score
        metrics["overall"] = round(sum(metrics.values()) / len(metrics), 4)

        logger.info(f"Evaluation complete: {metrics}")
        return metrics

    def _evaluate_quality(
        self,
        prompt: str,
        response: str,
        expected_answer: Optional[str] = None,
        context: Optional[str] = None,
        query: Optional[str] = None,
    ) -> float:
        """
        Evaluate overall response quality

        Args:
            prompt: The prompt used
            response: The model's response
            expected_answer: Expected answer
            context: Context provided
            query: User query

        Returns:
            Quality score (0-1)
        """
        if not response or not response.strip():
            return 0.0

        quality_score = 1.0

        # Check for common issues
        issues = []

        # Check if response is too short
        if len(response.strip()) < 20:
            issues.append("Too short")
            quality_score -= 0.2

        # Check for repeated content
        words = response.split()
        if len(words) > 0:
            unique_words = len(set(words))
            repetition_ratio = 1 - (unique_words / len(words))
            if repetition_ratio > 0.5:
                issues.append("High repetition")
                quality_score -= 0.3

        # Check for empty or placeholder responses
        placeholder_patterns = [
            r"^(I don't know|I'm not sure|I cannot answer).",
            r"^(Sorry|Apologies).*(cannot|can't|unable).",
        ]

        for pattern in placeholder_patterns:
            if re.match(pattern, response, re.IGNORECASE):
                issues.append("Placeholder response")
                quality_score -= 0.4
                break

        # Ensure score doesn't go below 0
        quality_score = max(0.0, quality_score)

        if issues:
            logger.debug(f"Quality issues detected: {issues}")

        return quality_score

    def _evaluate_relevance(
        self,
        prompt: str,
        response: str,
        expected_answer: Optional[str] = None,
        context: Optional[str] = None,
        query: Optional[str] = None,
    ) -> float:
        """
        Evaluate response relevance to query

        Args:
            prompt: The prompt used
            response: The model's response
            expected_answer: Expected answer
            context: Context provided
            query: User query

        Returns:
            Relevance score (0-1)
        """
        if not query:
            return 1.0  # Can't evaluate relevance without query

        if not response or not response.strip():
            return 0.0

        relevance_score = 1.0

        # Extract key terms from query
        query_terms = self._extract_key_terms(query)

        # Check if response contains key terms from query
        response_lower = response.lower()

        if query_terms:
            terms_found = sum(1 for term in query_terms if term.lower() in response_lower)
            term_coverage = terms_found / len(query_terms)

            # Penalize if response doesn't address key query terms
            if term_coverage < 0.3:
                relevance_score -= 0.4
            elif term_coverage < 0.6:
                relevance_score -= 0.2

        # Check if response directly addresses the question
        question_patterns = [
            r"^(how|what|why|when|where|who|which|can|could|would|should|is|are|do|does|did)",
        ]

        for pattern in question_patterns:
            if re.match(pattern, query, re.IGNORECASE):
                # Response should provide an answer, not just repeat the question
                if query.lower() in response.lower()[:100]:
                    relevance_score -= 0.3
                break

        # Ensure score doesn't go below 0
        relevance_score = max(0.0, relevance_score)

        return relevance_score

    def _evaluate_coherence(
        self,
        prompt: str,
        response: str,
        expected_answer: Optional[str] = None,
        context: Optional[str] = None,
        query: Optional[str] = None,
    ) -> float:
        """
        Evaluate logical coherence of response

        Args:
            prompt: The prompt used
            response: The model's response
            expected_answer: Expected answer
            context: Context provided
            query: User query

        Returns:
            Coherence score (0-1)
        """
        if not response or not response.strip():
            return 0.0

        coherence_score = 1.0

        # Check for contradictions
        contradiction_patterns = [
            r"however.*however",
            r"but.*but",
            r"although.*although",
        ]

        for pattern in contradiction_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                coherence_score -= 0.2
                break

        # Check for sentence structure
        sentences = re.split(r"[.!?]+", response)
        sentences = [s.strip() for s in sentences if s.strip()]

        if sentences:
            # Check for very long sentences (hard to follow)
            long_sentences = [s for s in sentences if len(s.split()) > 50]
            if len(long_sentences) / len(sentences) > 0.3:
                coherence_score -= 0.2

            # Check for very short sentences (choppy)
            short_sentences = [s for s in sentences if len(s.split()) < 5]
            if len(short_sentences) / len(sentences) > 0.5:
                coherence_score -= 0.1

        # Check for logical flow indicators
        flow_indicators = [
            "therefore",
            "consequently",
            "thus",
            "hence",
            "accordingly",
            "furthermore",
            "moreover",
            "in addition",
            "additionally",
            "however",
            "nevertheless",
            "on the other hand",
            "first",
            "second",
            "third",
            "finally",
            "lastly",
        ]

        response_lower = response.lower()
        flow_indicator_count = sum(
            1 for indicator in flow_indicators if indicator in response_lower
        )

        if flow_indicator_count > 0:
            # Good use of flow indicators
            coherence_score += min(0.1, flow_indicator_count * 0.02)

        # Ensure score doesn't exceed 1 or go below 0
        coherence_score = max(0.0, min(1.0, coherence_score))

        return coherence_score

    def _evaluate_completeness(
        self,
        prompt: str,
        response: str,
        expected_answer: Optional[str] = None,
        context: Optional[str] = None,
        query: Optional[str] = None,
    ) -> float:
        """
        Evaluate information completeness

        Args:
            prompt: The prompt used
            response: The model's response
            expected_answer: Expected answer
            context: Context provided
            query: User query

        Returns:
            Completeness score (0-1)
        """
        if not response or not response.strip():
            return 0.0

        completeness_score = 1.0

        # If expected answer is provided, compare with it
        if expected_answer:
            similarity = self._calculate_similarity(response, expected_answer)
            completeness_score = similarity

        # Check if response acknowledges missing information
        acknowledgment_patterns = [
            r"(i don't have enough|insufficient|limited) information",
            r"(not provided|not mentioned|not available) in the (context|sources)",
            r"(cannot|unable to) answer",
        ]

        response_lower = response.lower()
        has_acknowledgment = any(
            re.search(pattern, response_lower) for pattern in acknowledgment_patterns
        )

        # If context is provided but response doesn't use it, penalize
        if context and not has_acknowledgment:
            context_terms = self._extract_key_terms(context)

            if context_terms:
                context_coverage = sum(
                    1 for term in context_terms if term.lower() in response_lower
                ) / len(context_terms)

                if context_coverage < 0.2:
                    completeness_score -= 0.3
                elif context_coverage < 0.5:
                    completeness_score -= 0.1

        # Check if response provides actionable information
        actionable_patterns = [
            r"(step|first|then|next|finally)",
            r"(you can|to do this|follow these)",
            r"(recommended|suggested|advised)",
        ]

        if query and any(
            re.search(pattern, response_lower, re.IGNORECASE) for pattern in actionable_patterns
        ):
            # Good: provides actionable information
            completeness_score += 0.1

        # Ensure score doesn't exceed 1 or go below 0
        completeness_score = max(0.0, min(1.0, completeness_score))

        return completeness_score

    def _extract_key_terms(self, text: str) -> List[str]:
        """
        Extract key terms from text

        Args:
            text: Input text

        Returns:
            List of key terms
        """
        # Remove common stop words
        stop_words = {
            "a",
            "an",
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "dare",
            "how",
            "what",
            "why",
            "when",
            "where",
            "who",
            "which",
            "that",
            "this",
            "it",
            "i",
            "you",
            "he",
            "she",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
        }

        # Tokenize and filter
        words = re.findall(r"\b\w+\b", text.lower())
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]

        return key_terms

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts (simple Jaccard similarity)

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score (0-1)
        """
        # Extract key terms from both texts
        terms1 = set(self._extract_key_terms(text1))
        terms2 = set(self._extract_key_terms(text2))

        # Calculate Jaccard similarity
        if not terms1 and not terms2:
            return 1.0

        if not terms1 or not terms2:
            return 0.0

        intersection = len(terms1 & terms2)
        union = len(terms1 | terms2)

        similarity = intersection / union if union > 0 else 0.0

        return similarity

    def batch_evaluate(self, evaluations: List[Dict[str, Any]]) -> List[Dict[str, float]]:
        """
        Batch evaluate multiple prompts

        Args:
            evaluations: List of evaluation dictionaries

        Returns:
            List of evaluation results
        """
        results = []

        for evaluation in evaluations:
            try:
                result = self.evaluate(**evaluation)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch evaluation: {e}")
                results.append(
                    {
                        "quality": 0.0,
                        "relevance": 0.0,
                        "coherence": 0.0,
                        "completeness": 0.0,
                        "overall": 0.0,
                        "error": str(e),
                    }
                )

        return results

    def aggregate_metrics(
        self, metrics_list: List[Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """
        Aggregate metrics across multiple evaluations

        Args:
            metrics_list: List of metrics dictionaries

        Returns:
            Aggregated metrics (average, min, max, std)
        """
        if not metrics_list:
            return {}

        aggregated = {}

        # Get all metric names
        metric_names = metrics_list[0].keys()

        for metric_name in metric_names:
            values = [m[metric_name] for m in metrics_list if metric_name in m]

            if values:
                aggregated[metric_name] = {
                    "average": round(sum(values) / len(values), 4),
                    "min": round(min(values), 4),
                    "max": round(max(values), 4),
                    "count": len(values),
                }

        return aggregated


# Global evaluator instance
evaluator = PromptEvaluator()
