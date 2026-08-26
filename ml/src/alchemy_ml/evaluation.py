"""Evaluation pipeline for AlchemyCLI AI.

Measures retrieval quality (Recall@K, MRR, Precision@K),
intent classification accuracy, and safety classification.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np

from .inference import InferenceEngine
from .models import EvaluationMetrics, TrainingExample
from .safety import classify_risk

logger = logging.getLogger(__name__)


class Evaluator:
    """Evaluates the ML model on a test dataset."""

    def __init__(self, engine: InferenceEngine):
        self.engine = engine

    def evaluate(
        self,
        test_data: list[TrainingExample],
        top_k_values: list[int] | None = None,
    ) -> EvaluationMetrics:
        """Run full evaluation on test data.

        Args:
            test_data: List of TrainingExample with query → expected command_id.
            top_k_values: K values for Recall@K and Precision@K.

        Returns:
            EvaluationMetrics with all scores.
        """
        top_k_values = top_k_values or [1, 3, 5]
        max_k = max(top_k_values)

        if not test_data:
            logger.warning("Empty test data")
            return EvaluationMetrics()

        logger.info("Evaluating on %d queries...", len(test_data))
        start = time.monotonic()

        recall_hits: dict[int, int] = {k: 0 for k in top_k_values}
        precision_sums: dict[int, float] = {k: 0.0 for k in top_k_values}
        reciprocal_ranks: list[float] = []
        intent_correct = 0
        intent_total = 0

        for example in test_data:
            response = self.engine.ask(
                query=example.query,
                top_k=max_k,
                mode="hybrid",
                explain=False,
            )

            result_ids = [r.command_id for r in response.results]

            # Recall@K
            for k in top_k_values:
                if example.command_id in result_ids[:k]:
                    recall_hits[k] += 1

            # Precision@K
            for k in top_k_values:
                relevant = sum(1 for r_id in result_ids[:k] if r_id == example.command_id)
                precision_sums[k] += relevant / k if k > 0 else 0

            # MRR
            try:
                rank = result_ids.index(example.command_id) + 1
                reciprocal_ranks.append(1.0 / rank)
            except ValueError:
                reciprocal_ranks.append(0.0)

            # Intent accuracy (if classifier available)
            if example.intent and response.results:
                intent_total += 1
                if response.results[0].intent == example.intent:
                    intent_correct += 1

        n = len(test_data)
        elapsed = time.monotonic() - start

        metrics = EvaluationMetrics(
            recall_at_1=recall_hits.get(1, 0) / n if n > 0 else 0,
            recall_at_3=recall_hits.get(3, 0) / n if n > 0 else 0,
            recall_at_5=recall_hits.get(5, 0) / n if n > 0 else 0,
            mrr=float(np.mean(reciprocal_ranks)) if reciprocal_ranks else 0,
            precision_at_1=precision_sums.get(1, 0) / n if n > 0 else 0,
            precision_at_3=precision_sums.get(3, 0) / n if n > 0 else 0,
            intent_accuracy=intent_correct / intent_total if intent_total > 0 else 0,
            safety_accuracy=0.0,  # Computed separately
            num_queries=n,
            num_commands=self.engine.command_count,
            dataset_version="2026.08",
        )

        logger.info(
            "Evaluation complete in %.1fs. Recall@1=%.3f, Recall@3=%.3f, MRR=%.3f",
            elapsed, metrics.recall_at_1, metrics.recall_at_3, metrics.mrr,
        )

        return metrics

    def evaluate_safety(self, test_data: list[dict[str, str]]) -> float:
        """Evaluate safety classification accuracy.

        Args:
            test_data: List of dicts with 'command' and 'expected_risk'.

        Returns:
            Accuracy as float in [0, 1].
        """
        if not test_data:
            return 0.0

        correct = 0
        for entry in test_data:
            predicted = classify_risk(entry["command"])
            if predicted.value == entry["expected_risk"]:
                correct += 1

        accuracy = correct / len(test_data)
        logger.info("Safety accuracy: %.3f (%d/%d)", accuracy, correct, len(test_data))
        return accuracy

    def run_regression_tests(self, regression_path: Path) -> dict[str, Any]:
        """Run regression tests from a JSONL file.

        Each line: {"query": "...", "expected": "command-id"}

        Returns:
            Dict with pass/fail counts and failures.
        """
        if not regression_path.exists():
            logger.warning("Regression file not found: %s", regression_path)
            return {"passed": 0, "failed": 0, "total": 0, "failures": []}

        passed = 0
        failed = 0
        failures: list[dict[str, str]] = []

        with open(regression_path) as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON on line %d", line_num)
                    continue

                query = entry.get("query", "")
                expected_id = entry.get("expected", "")

                if not query or not expected_id:
                    continue

                response = self.engine.ask(query=query, top_k=1, mode="hybrid")
                if response.results and response.results[0].command_id == expected_id:
                    passed += 1
                else:
                    failed += 1
                    actual = response.results[0].command_id if response.results else "NO_RESULT"
                    failures.append({
                        "query": query,
                        "expected": expected_id,
                        "actual": actual,
                    })

        total = passed + failed
        logger.info("Regression: %d/%d passed (%.1f%%)", passed, total, passed / total * 100 if total else 0)

        return {
            "passed": passed,
            "failed": failed,
            "total": total,
            "pass_rate": passed / total if total > 0 else 0,
            "failures": failures,
        }

    def generate_report(
        self,
        metrics: EvaluationMetrics,
        output_dir: Path,
        safety_accuracy: float = 0.0,
    ) -> None:
        """Generate evaluation report files.

        Creates:
        - evaluation.json
        - evaluation.md
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        metrics.safety_accuracy = safety_accuracy

        # JSON report
        json_path = output_dir / "evaluation.json"
        with open(json_path, "w") as f:
            json.dump(metrics.model_dump(), f, indent=2)

        # Markdown report
        md_path = output_dir / "evaluation.md"
        with open(md_path, "w") as f:
            f.write("# AlchemyCLI AI — Evaluation Report\n\n")
            f.write(f"**Dataset Version:** {metrics.dataset_version}\n\n")
            f.write(f"**Commands:** {metrics.num_commands}\n\n")
            f.write(f"**Test Queries:** {metrics.num_queries}\n\n")
            f.write("## Retrieval Metrics\n\n")
            f.write(f"| Metric | Score |\n")
            f.write(f"|--------|-------|\n")
            f.write(f"| Recall@1 | {metrics.recall_at_1:.1%} |\n")
            f.write(f"| Recall@3 | {metrics.recall_at_3:.1%} |\n")
            f.write(f"| Recall@5 | {metrics.recall_at_5:.1%} |\n")
            f.write(f"| MRR | {metrics.mrr:.3f} |\n")
            f.write(f"| Precision@1 | {metrics.precision_at_1:.1%} |\n")
            f.write(f"| Precision@3 | {metrics.precision_at_3:.1%} |\n")
            f.write(f"\n## Classification Metrics\n\n")
            f.write(f"| Metric | Score |\n")
            f.write(f"|--------|-------|\n")
            f.write(f"| Intent Accuracy | {metrics.intent_accuracy:.1%} |\n")
            f.write(f"| Safety Accuracy | {metrics.safety_accuracy:.1%} |\n")

        logger.info("Reports saved to %s", output_dir)


def load_test_data(path: Path) -> list[TrainingExample]:
    """Load test data from JSONL file."""
    examples: list[TrainingExample] = []
    if not path.exists():
        return examples

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                examples.append(TrainingExample(**data))
            except Exception as e:
                logger.warning("Invalid test example: %s", e)

    return examples
