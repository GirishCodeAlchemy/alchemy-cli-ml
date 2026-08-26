"""ML CLI commands for AlchemyCLI AI.

Provides commands for dataset building, training, evaluation,
and benchmarking.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import click

from .config import get_config


@click.group()
def main() -> None:
    """AlchemyCLI AI — ML Pipeline Commands."""
    pass


@main.command()
def info() -> None:
    """Show model and dataset information."""
    from .inference import InferenceEngine

    engine = InferenceEngine()
    engine.load_commands()

    model_info = engine.get_model_info()
    techs = engine.get_all_technologies()
    categories = engine.get_all_categories()

    click.echo("\nAlchemyCLI AI — Model Info\n")
    click.echo(f"  Commands:       {model_info.num_commands}")
    click.echo(f"  Technologies:   {len(techs)}")
    click.echo(f"  Intents:        {model_info.num_intents}")
    click.echo(f"  Dataset:        {model_info.dataset_version}")
    click.echo(f"\n  Technologies:")
    for tech in techs:
        cmds = engine.get_commands_by_technology(tech)
        click.echo(f"    {tech}: {len(cmds)} commands")


@main.command()
@click.option("--output", "-o", default=None, help="Output directory for processed data")
def dataset(output: str | None) -> None:
    """Build the training dataset from knowledge base."""
    from .dataset import build_dataset

    config = get_config()
    output_dir = Path(output) if output else config.data_dir / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    stats = build_dataset(config.knowledge_dir, output_dir, config)
    click.echo(f"\nDataset built: {stats['total_examples']} examples from {stats['total_commands']} commands")


@main.command()
def embeddings() -> None:
    """Generate embeddings and build FAISS index."""
    from .inference import InferenceEngine

    engine = InferenceEngine()
    engine.load_commands()
    click.echo(f"Loaded {engine.command_count} commands")

    click.echo("Building index...")
    start = time.monotonic()
    engine.build_index()
    elapsed = time.monotonic() - start
    click.echo(f"Index built in {elapsed:.1f}s")

    engine.save_index()
    click.echo("Index saved.")


@main.command()
def train() -> None:
    """Train the intent classifier."""
    from .classifier import IntentClassifier
    from .dataset import load_training_data

    config = get_config()
    data_path = config.data_dir / "processed" / "train.jsonl"

    if not data_path.exists():
        click.echo("Training data not found. Run 'alchemyai-ml dataset' first.", err=True)
        sys.exit(1)

    queries, technologies, intents = load_training_data(data_path)
    click.echo(f"Training on {len(queries)} examples...")

    classifier = IntentClassifier()
    metrics = classifier.fit(queries, technologies, intents)

    classifier.save(config.classifier_path)
    click.echo(f"\nTraining complete:")
    click.echo(f"  Tech accuracy:    {metrics['technology_accuracy']:.1%}")
    click.echo(f"  Intent accuracy:  {metrics['intent_accuracy']:.1%}")
    click.echo(f"  Technologies:     {metrics['num_technologies']}")
    click.echo(f"  Intents:          {metrics['num_intents']}")


@main.command()
@click.option("--test-file", "-t", default=None, help="Path to test JSONL file")
def evaluate(test_file: str | None) -> None:
    """Evaluate model on test data."""
    from .evaluation import Evaluator, load_test_data
    from .inference import InferenceEngine

    config = get_config()
    test_path = Path(test_file) if test_file else config.data_dir / "processed" / "test.jsonl"

    if not test_path.exists():
        click.echo(f"Test data not found: {test_path}", err=True)
        sys.exit(1)

    test_data = load_test_data(test_path)
    click.echo(f"Loaded {len(test_data)} test examples")

    engine = InferenceEngine()
    engine.initialize()

    evaluator = Evaluator(engine)
    metrics = evaluator.evaluate(test_data)

    click.echo(f"\nAlchemyCLI AI — Evaluation Results\n")
    click.echo(f"  Recall@1:     {metrics.recall_at_1:.1%}")
    click.echo(f"  Recall@3:     {metrics.recall_at_3:.1%}")
    click.echo(f"  Recall@5:     {metrics.recall_at_5:.1%}")
    click.echo(f"  MRR:          {metrics.mrr:.3f}")
    click.echo(f"  Precision@1:  {metrics.precision_at_1:.1%}")
    click.echo(f"  Precision@3:  {metrics.precision_at_3:.1%}")
    click.echo(f"  Intent Acc:   {metrics.intent_accuracy:.1%}")

    report_dir = config.ml_root / "reports"
    evaluator.generate_report(metrics, report_dir)
    click.echo(f"\nReports saved to {report_dir}")


@main.command()
def benchmark() -> None:
    """Run benchmark and measure latency."""
    from .evaluation import Evaluator, load_test_data
    from .inference import InferenceEngine

    config = get_config()
    bench_path = config.data_dir / "benchmark.jsonl"

    if not bench_path.exists():
        click.echo(f"Benchmark data not found: {bench_path}", err=True)
        sys.exit(1)

    engine = InferenceEngine()
    engine.initialize()

    test_data = load_test_data(bench_path)
    click.echo(f"Loaded {len(test_data)} benchmark queries\n")

    # Measure latency
    latencies = []
    for ex in test_data[:50]:
        start = time.monotonic()
        engine.ask(query=ex.query, top_k=5)
        latencies.append((time.monotonic() - start) * 1000)

    import numpy as np
    latencies_arr = np.array(latencies)

    click.echo("AlchemyCLI AI — Benchmark\n")
    click.echo(f"  Queries:     {len(test_data)}")
    click.echo(f"  p50 latency: {np.percentile(latencies_arr, 50):.1f}ms")
    click.echo(f"  p90 latency: {np.percentile(latencies_arr, 90):.1f}ms")
    click.echo(f"  p99 latency: {np.percentile(latencies_arr, 99):.1f}ms")
    click.echo(f"  Mean:        {latencies_arr.mean():.1f}ms")

    # Accuracy
    evaluator = Evaluator(engine)
    metrics = evaluator.evaluate(test_data)
    click.echo(f"\n  Recall@1:    {metrics.recall_at_1:.1%}")
    click.echo(f"  Recall@3:    {metrics.recall_at_3:.1%}")
    click.echo(f"  MRR:         {metrics.mrr:.3f}")


@main.command(name="regression")
def regression_test() -> None:
    """Run regression tests."""
    from .evaluation import Evaluator
    from .inference import InferenceEngine

    config = get_config()
    regression_path = config.ml_root / "tests" / "regression.jsonl"

    if not regression_path.exists():
        click.echo(f"Regression file not found: {regression_path}", err=True)
        sys.exit(1)

    engine = InferenceEngine()
    engine.initialize()

    evaluator = Evaluator(engine)
    results = evaluator.run_regression_tests(regression_path)

    click.echo(f"\nRegression Tests: {results['passed']}/{results['total']} passed")
    if results["failures"]:
        click.echo("\nFailures:")
        for f in results["failures"]:
            click.echo(f"  Query: {f['query']}")
            click.echo(f"  Expected: {f['expected']}")
            click.echo(f"  Actual: {f['actual']}\n")

    if results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
