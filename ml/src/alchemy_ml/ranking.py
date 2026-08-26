"""Hybrid ranking for AlchemyCLI AI.

Combines semantic similarity, keyword matching, technology
detection, intent classification, and tag matching into a
single ranked result set.
"""

from __future__ import annotations

import logging
from typing import Any

from .config import get_config
from .models import Command, RiskLevel, SearchExplanation, SearchResult
from .preprocessing import (
    compute_keyword_overlap,
    detect_technology,
    extract_keywords,
)

logger = logging.getLogger(__name__)


class HybridRanker:
    """Ranks command candidates using a weighted combination of signals."""

    def __init__(self, weights: dict[str, float] | None = None):
        """Initialize the ranker.

        Args:
            weights: Optional override for ranking weights.
        """
        config = get_config()
        ranking = config.ranking

        self.weights = weights or {
            "semantic": ranking.semantic_weight,
            "keyword": ranking.keyword_weight,
            "technology": ranking.technology_weight,
            "intent": ranking.intent_weight,
            "tag": ranking.tag_weight,
        }

        # Validate weights sum to ~1.0
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning("Ranking weights sum to %.3f (expected 1.0), normalizing", total)
            self.weights = {k: v / total for k, v in self.weights.items()}

    def rank(
        self,
        candidates: list[tuple[Command, float]],
        query: str,
        detected_tech: str | None = None,
        detected_intent: str | None = None,
        top_k: int = 10,
    ) -> list[SearchResult]:
        """Rank candidates and return top results.

        Args:
            candidates: List of (Command, semantic_score) tuples from retrieval.
            query: The original user query.
            detected_tech: Technology detected from query preprocessing.
            detected_intent: Intent detected from classifier.
            top_k: Number of results to return.

        Returns:
            Ranked list of SearchResult objects.
        """
        if not candidates:
            return []

        query_keywords = extract_keywords(query)
        query_tech = detected_tech or detect_technology(query)

        scored: list[tuple[Command, SearchExplanation]] = []

        for command, semantic_score in candidates:
            explanation = self._compute_scores(
                command=command,
                query_keywords=query_keywords,
                query_tech=query_tech,
                query_intent=detected_intent,
                semantic_score=semantic_score,
            )
            scored.append((command, explanation))

        # Sort by final score descending
        scored.sort(key=lambda x: x[1].final_score, reverse=True)

        # Convert to SearchResult objects
        results: list[SearchResult] = []
        seen_commands: set[str] = set()

        for command, explanation in scored[:top_k]:
            # Deduplicate by command text
            if command.command in seen_commands:
                continue
            seen_commands.add(command.command)

            # Find related commands (same technology, different command)
            related = [
                c.command
                for c, _ in candidates
                if c.technology == command.technology
                and c.command != command.command
                and c.command not in seen_commands
            ][:3]

            result = SearchResult(
                command_id=command.id,
                command=command.command,
                name=command.name,
                description=command.description,
                technology=command.technology,
                category=command.category,
                intent=command.intent,
                confidence=explanation.final_score,
                risk=command.risk,
                tags=command.tags,
                documentation_url=command.doc_url,
                related_commands=related,
                explanation=explanation,
            )
            results.append(result)

        return results

    def _compute_scores(
        self,
        command: Command,
        query_keywords: list[str],
        query_tech: str | None,
        query_intent: str | None,
        semantic_score: float,
    ) -> SearchExplanation:
        """Compute all scoring signals for a candidate."""
        # 1. Semantic score (already computed by retrieval)
        semantic = max(0.0, min(1.0, semantic_score))

        # 2. Keyword overlap
        cmd_keywords = extract_keywords(command.searchable_text)
        keyword = compute_keyword_overlap(query_keywords, cmd_keywords)

        # 3. Technology match
        tech_score = 0.0
        if query_tech and command.technology.lower() == query_tech.lower():
            tech_score = 1.0
        elif query_tech:
            # Partial match — technology detected but doesn't match
            tech_score = 0.0

        # 4. Intent match
        intent_score = 0.0
        if query_intent and command.intent.lower() == query_intent.lower():
            intent_score = 1.0
        elif query_intent:
            # Partial match on intent words
            intent_words = set(query_intent.lower().replace("_", " ").split())
            cmd_intent_words = set(command.intent.lower().replace("_", " ").split())
            if intent_words & cmd_intent_words:
                intent_score = len(intent_words & cmd_intent_words) / len(intent_words | cmd_intent_words)

        # 5. Tag match
        tag_score = 0.0
        if query_keywords and command.tags:
            query_set = set(query_keywords)
            tag_set = set(t.lower() for t in command.tags)
            overlap = query_set & tag_set
            if overlap:
                tag_score = len(overlap) / max(len(query_set), 1)

        # Weighted final score
        final = (
            self.weights["semantic"] * semantic
            + self.weights["keyword"] * keyword
            + self.weights["technology"] * tech_score
            + self.weights["intent"] * intent_score
            + self.weights["tag"] * tag_score
        )

        # Clamp to [0, 1]
        final = max(0.0, min(1.0, final))

        matched_tags = []
        if command.tags:
            matched_tags = [t for t in command.tags if t.lower() in set(query_keywords)]

        return SearchExplanation(
            technology_detected=query_tech or "",
            intent_detected=query_intent or "",
            matched_tags=matched_tags,
            semantic_score=round(semantic, 4),
            keyword_score=round(keyword, 4),
            technology_score=round(tech_score, 4),
            intent_score=round(intent_score, 4),
            tag_score=round(tag_score, 4),
            final_score=round(final, 4),
        )


def compute_confidence_label(confidence: float) -> str:
    """Map a confidence score to a human-readable label."""
    config = get_config()

    if confidence >= config.high_confidence:
        return "Very likely match"
    elif confidence >= config.medium_confidence:
        return "Likely match"
    elif confidence >= config.confidence_threshold:
        return "Possible match"
    else:
        return "Low confidence"


def compute_risk_display(risk: RiskLevel) -> dict[str, str]:
    """Get display properties for a risk level."""
    if risk == RiskLevel.DANGEROUS:
        return {"label": "DANGEROUS", "icon": "🔴", "color": "red"}
    elif risk == RiskLevel.WARNING:
        return {"label": "WARNING", "icon": "🟡", "color": "yellow"}
    else:
        return {"label": "SAFE", "icon": "🟢", "color": "green"}
