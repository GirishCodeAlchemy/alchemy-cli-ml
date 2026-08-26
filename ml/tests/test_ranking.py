"""Tests for hybrid ranking."""

import pytest
from alchemy_ml.models import Command, RiskLevel
from alchemy_ml.ranking import HybridRanker, compute_confidence_label, compute_risk_display


class TestHybridRanker:
    def setup_method(self):
        self.ranker = HybridRanker()

    def _make_cmd(self, id: str, tech: str, intent: str, tags: list[str]) -> Command:
        return Command(
            id=id,
            technology=tech,
            category="test",
            name=f"Command {id}",
            intent=intent,
            command=f"test-cmd-{id}",
            description=f"Description for {id}",
            tags=tags,
            risk=RiskLevel.SAFE,
        )

    def test_rank_by_semantic_score(self):
        cmd1 = self._make_cmd("a", "kubernetes", "list_pods", ["pods"])
        cmd2 = self._make_cmd("b", "kubernetes", "list_pods", ["pods"])

        candidates = [(cmd1, 0.9), (cmd2, 0.5)]
        results = self.ranker.rank(candidates, "list kubernetes pods")

        assert len(results) == 2
        assert results[0].command_id == "a"
        assert results[0].confidence > results[1].confidence

    def test_technology_boost(self):
        cmd1 = self._make_cmd("a", "kubernetes", "restart", ["restart"])
        cmd2 = self._make_cmd("b", "docker", "restart", ["restart"])

        candidates = [(cmd1, 0.7), (cmd2, 0.75)]
        results = self.ranker.rank(
            candidates, "restart kubernetes deployment",
            detected_tech="kubernetes",
        )

        # cmd1 should rank higher due to technology match despite lower semantic score
        assert results[0].command_id == "a"

    def test_empty_candidates(self):
        results = self.ranker.rank([], "test query")
        assert results == []

    def test_deduplication(self):
        cmd1 = Command(
            id="a", technology="k8s", category="t", name="A",
            intent="i", command="same command", description="d",
            risk=RiskLevel.SAFE,
        )
        cmd2 = Command(
            id="b", technology="k8s", category="t", name="B",
            intent="i", command="same command", description="d",
            risk=RiskLevel.SAFE,
        )
        results = self.ranker.rank([(cmd1, 0.9), (cmd2, 0.8)], "test")
        assert len(results) == 1


class TestConfidenceLabel:
    def test_high(self):
        assert compute_confidence_label(0.95) == "Very likely match"

    def test_medium(self):
        assert compute_confidence_label(0.80) == "Likely match"

    def test_low(self):
        assert compute_confidence_label(0.60) == "Possible match"

    def test_very_low(self):
        assert compute_confidence_label(0.30) == "Low confidence"


class TestRiskDisplay:
    def test_safe(self):
        d = compute_risk_display(RiskLevel.SAFE)
        assert d["label"] == "SAFE"
        assert d["color"] == "green"

    def test_warning(self):
        d = compute_risk_display(RiskLevel.WARNING)
        assert d["label"] == "WARNING"

    def test_dangerous(self):
        d = compute_risk_display(RiskLevel.DANGEROUS)
        assert d["label"] == "DANGEROUS"
        assert d["color"] == "red"
