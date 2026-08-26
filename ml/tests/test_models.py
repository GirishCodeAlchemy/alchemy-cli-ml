"""Tests for data models."""

import pytest
from alchemy_ml.models import Command, RiskLevel, SearchResult, SearchExplanation


class TestCommand:
    def test_create(self):
        cmd = Command(
            id="test-cmd",
            technology="kubernetes",
            category="pods",
            name="Get pods",
            intent="list_pods",
            command="kubectl get pods",
            description="List all pods.",
            tags=["kubernetes", "pods"],
            risk=RiskLevel.SAFE,
        )
        assert cmd.id == "test-cmd"
        assert cmd.technology == "kubernetes"
        assert cmd.risk == RiskLevel.SAFE

    def test_searchable_text(self):
        cmd = Command(
            id="test-cmd",
            technology="kubernetes",
            category="pods",
            name="Get pods",
            intent="list_pods",
            command="kubectl get pods",
            description="List all pods in the namespace.",
            tags=["kubernetes", "pods", "list"],
            aliases=["show pods", "get pods"],
            examples=[{"query": "how do I list pods"}],
        )
        text = cmd.searchable_text
        assert "Get pods" in text
        assert "kubernetes" in text
        assert "list pods" in text
        assert "show pods" in text
        assert "how do I list pods" in text

    def test_risk_enum(self):
        assert RiskLevel.SAFE.value == "safe"
        assert RiskLevel.WARNING.value == "warning"
        assert RiskLevel.DANGEROUS.value == "dangerous"


class TestSearchResult:
    def test_create(self):
        result = SearchResult(
            command_id="test",
            command="kubectl get pods",
            name="Get pods",
            description="List pods",
            technology="kubernetes",
            category="pods",
            intent="list_pods",
            confidence=0.95,
            risk=RiskLevel.SAFE,
        )
        assert result.confidence == 0.95
        assert result.risk == RiskLevel.SAFE

    def test_with_explanation(self):
        exp = SearchExplanation(
            technology_detected="kubernetes",
            semantic_score=0.92,
            final_score=0.95,
        )
        result = SearchResult(
            command_id="test",
            command="kubectl get pods",
            name="Get pods",
            description="List pods",
            technology="kubernetes",
            category="pods",
            intent="list_pods",
            confidence=0.95,
            risk=RiskLevel.SAFE,
            explanation=exp,
        )
        assert result.explanation.semantic_score == 0.92
