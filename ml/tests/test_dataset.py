"""Tests for dataset generation."""

import pytest
from alchemy_ml.dataset import (
    generate_query_variations,
    generate_training_examples,
    split_dataset,
)
from alchemy_ml.models import Command, RiskLevel, TrainingExample


class TestGenerateQueryVariations:
    def test_includes_examples(self):
        cmd = Command(
            id="test", technology="kubernetes", category="pods",
            name="Get pods", intent="list_pods", command="kubectl get pods",
            description="List pods",
            examples=[{"query": "how do I list pods"}],
            risk=RiskLevel.SAFE,
        )
        variations = generate_query_variations(cmd)
        assert "how do I list pods" in variations

    def test_includes_aliases(self):
        cmd = Command(
            id="test", technology="kubernetes", category="pods",
            name="Get pods", intent="list_pods", command="kubectl get pods",
            description="List pods",
            aliases=["show pods", "get all pods"],
            risk=RiskLevel.SAFE,
        )
        variations = generate_query_variations(cmd)
        assert "show pods" in variations

    def test_generates_templates(self):
        cmd = Command(
            id="test", technology="kubernetes", category="pods",
            name="Get pods", intent="list_pods", command="kubectl get pods",
            description="List pods",
            risk=RiskLevel.SAFE,
        )
        variations = generate_query_variations(cmd)
        assert len(variations) >= 5  # Should generate multiple from templates

    def test_no_duplicates(self):
        cmd = Command(
            id="test", technology="kubernetes", category="pods",
            name="Get pods", intent="list_pods", command="kubectl get pods",
            description="List pods",
            aliases=["list pods", "list pods"],  # Duplicate alias
            risk=RiskLevel.SAFE,
        )
        variations = generate_query_variations(cmd)
        lowered = [v.lower().strip() for v in variations]
        assert len(lowered) == len(set(lowered))


class TestSplitDataset:
    def test_no_leakage(self):
        examples = [
            TrainingExample(query=f"query {i}", command_id=f"cmd-{i // 3}", technology="test", intent="test")
            for i in range(30)
        ]
        train, val, test = split_dataset(examples, seed=42)

        train_ids = {ex.command_id for ex in train}
        val_ids = {ex.command_id for ex in val}
        test_ids = {ex.command_id for ex in test}

        # No command should appear in both train and test
        assert train_ids.isdisjoint(test_ids)
        assert train_ids.isdisjoint(val_ids)
        assert val_ids.isdisjoint(test_ids)

    def test_split_ratios(self):
        examples = [
            TrainingExample(query=f"q{i}", command_id=f"c{i}", technology="t", intent="i")
            for i in range(100)
        ]
        train, val, test = split_dataset(examples, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15)

        total = len(train) + len(val) + len(test)
        assert total == 100
