"""
Response evaluator for Azure AI Infrastructure Platform

This module provides:
- Response quality metrics
- Relevance scoring
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ResponseEvaluator:
    """Evaluate response quality and relevance"""

    def __init__(self):
        """Initialize response evaluator"""
        pass

    def evaluate_response_quality(
        self, response: str, question: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate the quality of a response

        Args:
            response: The response to evaluate
            question: The original question (optional)

        Returns:
            Dictionary with quality metrics
        """
        metrics = {
            "length": len(response),
            "word_count": len(response.split()),
            "sentence_count": len(re.split(r"[.!?]+", response)),
            "has_structure": self._has_structure(response),
            "has_explanation": self._has_explanation(response),
            "is_concise": self._is_concise(response),
            "relevance_score": 0.0,
        }

        if question:
            metrics["relevance_score"] = self._calculate_relevance(response, question)

        return metrics

    def _has_structure(self, response: str) -> bool:
        """Check if response has good structure"""
        # Check for paragraphs, bullet points, or numbered lists
        has_paragraphs = len(response.split("\n\n")) > 1
        has_bullets = bool(re.search(r"[\*\-\•]\s", response))
        has_numbers = bool(re.search(r"\d+\.", response))

        return has_paragraphs or has_bullets or has_numbers

    def _has_explanation(self, response: str) -> bool:
        """Check if response provides explanations"""
        # Check for explanatory words
        explanation_words = ["because", "since", "therefore", "thus", "due to", "as a result"]
        return any(word in response.lower() for word in explanation_words)

    def _is_concise(self, response: str) -> bool:
        """Check if response is concise"""
        word_count = len(response.split())
        return 50 <= word_count <= 300

    def _calculate_relevance(self, response: str, question: str) -> float:
        """
        Calculate relevance score between response and question

        Args:
            response: The response
            question: The original question

        Returns:
            Relevance score (0-1)
        """
        # Simple keyword overlap relevance
        question_words = set(question.lower().split())
        response_words = set(response.lower().split())

        if not question_words:
            return 0.0

        overlap = len(question_words & response_words)
        relevance = overlap / len(question_words)

        return min(1.0, relevance * 2.0)  # Boost score slightly

    def evaluate_rag_response(
        self, answer: str, sources: List[Dict[str, Any]], query: str
    ) -> Dict[str, Any]:
        """
        Evaluate a RAG response

        Args:
            answer: The generated answer
            sources: List of source documents
            query: The original query

        Returns:
            Dictionary with RAG-specific metrics
        """
        metrics = self.evaluate_response_quality(answer, query)

        # RAG-specific metrics
        metrics["num_sources"] = len(sources)
        metrics["avg_source_score"] = (
            sum(s.get("score", 0) for s in sources) / len(sources) if sources else 0.0
        )
        metrics["answer_contains_citations"] = self._contains_citations(answer)

        return metrics

    def _contains_citations(self, text: str) -> bool:
        """Check if text contains citation markers"""
        citation_patterns = [
            r"\[source-\d+\]",
            r"\[citation:\d+\]",
            r"\[doc-\d+\]",
            r"\(source \d+\)",
        ]
        return any(re.search(pattern, text) for pattern in citation_patterns)
