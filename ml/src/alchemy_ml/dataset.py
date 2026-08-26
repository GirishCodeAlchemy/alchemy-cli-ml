"""Dataset building and training data generation for AlchemyCLI AI.

Generates query variations from structured command data,
creates training/validation/test splits, and produces
positive/negative pairs for embedding training.
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any

import yaml

from .config import Config, get_config
from .models import Command, TrainingExample

logger = logging.getLogger(__name__)

# Query templates for synthetic data generation
QUERY_TEMPLATES: list[str] = [
    "how do I {intent}",
    "how can I {intent}",
    "how to {intent}",
    "what command {intent}",
    "command to {intent}",
    "{technology} {intent}",
    "show me how to {intent}",
    "I need to {intent}",
    "I want to {intent}",
    "what is the command for {intent}",
    "best way to {intent}",
    "{intent} in {technology}",
    "{intent} using {technology}",
    "{intent} command",
    "{intent}",
]


def load_commands(knowledge_dir: Path) -> list[Command]:
    """Load all commands from knowledge base YAML files."""
    commands: list[Command] = []

    for yaml_file in sorted(knowledge_dir.rglob("*.yaml")):
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            if not isinstance(data, list):
                continue

            for entry in data:
                if isinstance(entry, dict):
                    try:
                        commands.append(Command(**entry))
                    except Exception as e:
                        logger.warning("Invalid command in %s: %s", yaml_file, e)
        except Exception as e:
            logger.error("Error loading %s: %s", yaml_file, e)

    logger.info("Loaded %d commands", len(commands))
    return commands


def generate_query_variations(command: Command) -> list[str]:
    """Generate natural language query variations for a command.

    Uses:
    1. Existing examples from the command
    2. Aliases
    3. Template-based generation
    """
    variations: list[str] = []

    # 1. Existing examples
    for ex in command.examples:
        if "query" in ex:
            variations.append(ex["query"])

    # 2. Aliases
    variations.extend(command.aliases)

    # 3. Template-based
    intent_text = command.intent.replace("_", " ")
    name_text = command.name.lower()

    for template in QUERY_TEMPLATES:
        try:
            q = template.format(
                intent=intent_text,
                technology=command.technology,
                name=name_text,
            )
            variations.append(q)
        except KeyError:
            # Template requires fields not available
            pass

    # Additional variations using name
    variations.append(f"how do I {name_text}")
    variations.append(f"{command.technology} {name_text}")
    variations.append(f"{name_text} in {command.technology}")

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for v in variations:
        v_lower = v.lower().strip()
        if v_lower not in seen:
            seen.add(v_lower)
            unique.append(v)

    return unique


def generate_training_examples(commands: list[Command]) -> list[TrainingExample]:
    """Generate training examples from all commands."""
    examples: list[TrainingExample] = []

    for cmd in commands:
        variations = generate_query_variations(cmd)
        for query in variations:
            examples.append(TrainingExample(
                query=query,
                command_id=cmd.id,
                technology=cmd.technology,
                intent=cmd.intent,
            ))

    logger.info("Generated %d training examples from %d commands", len(examples), len(commands))
    return examples


def generate_hard_negatives(
    commands: list[Command],
    negatives_per_command: int = 5,
) -> list[dict[str, Any]]:
    """Generate hard negative pairs for contrastive training.

    Hard negatives are commands from the same technology that
    are semantically close but incorrect.
    """
    # Group by technology
    by_tech: dict[str, list[Command]] = {}
    for cmd in commands:
        by_tech.setdefault(cmd.technology, []).append(cmd)

    pairs: list[dict[str, Any]] = []

    for cmd in commands:
        tech_commands = by_tech.get(cmd.technology, [])
        # Get negatives from same technology (hard negatives)
        negatives = [c for c in tech_commands if c.id != cmd.id]

        if len(negatives) > negatives_per_command:
            negatives = random.sample(negatives, negatives_per_command)

        for query in generate_query_variations(cmd)[:3]:  # Use a few queries per command
            for neg in negatives:
                pairs.append({
                    "query": query,
                    "positive_id": cmd.id,
                    "negative_id": neg.id,
                    "positive_text": cmd.searchable_text,
                    "negative_text": neg.searchable_text,
                })

    logger.info("Generated %d hard negative pairs", len(pairs))
    return pairs


def split_dataset(
    examples: list[TrainingExample],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    seed: int = 42,
) -> tuple[list[TrainingExample], list[TrainingExample], list[TrainingExample]]:
    """Split examples into train/val/test avoiding leakage.

    Splits by command_id so queries for the same command
    don't appear in both train and test.
    """
    random.seed(seed)

    # Group by command_id
    by_command: dict[str, list[TrainingExample]] = {}
    for ex in examples:
        by_command.setdefault(ex.command_id, []).append(ex)

    command_ids = list(by_command.keys())
    random.shuffle(command_ids)

    n = len(command_ids)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    train_ids = set(command_ids[:train_end])
    val_ids = set(command_ids[train_end:val_end])
    test_ids = set(command_ids[val_end:])

    train = [ex for ex in examples if ex.command_id in train_ids]
    val = [ex for ex in examples if ex.command_id in val_ids]
    test = [ex for ex in examples if ex.command_id in test_ids]

    random.shuffle(train)
    random.shuffle(val)
    random.shuffle(test)

    logger.info("Split: train=%d, val=%d, test=%d", len(train), len(val), len(test))
    return train, val, test


def save_jsonl(examples: list[TrainingExample], path: Path) -> None:
    """Save examples to JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for ex in examples:
            f.write(json.dumps(ex.model_dump()) + "\n")
    logger.info("Saved %d examples to %s", len(examples), path)


def load_training_data(path: Path) -> tuple[list[str], list[str], list[str]]:
    """Load training data from JSONL, returning (queries, technologies, intents)."""
    queries: list[str] = []
    technologies: list[str] = []
    intents: list[str] = []

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            queries.append(data["query"])
            technologies.append(data.get("technology", ""))
            intents.append(data.get("intent", ""))

    return queries, technologies, intents


def build_dataset(
    knowledge_dir: Path,
    output_dir: Path,
    config: Config | None = None,
) -> dict[str, int]:
    """Full dataset build pipeline.

    1. Load commands from knowledge base
    2. Generate query variations
    3. Split into train/val/test
    4. Save JSONL files

    Returns:
        Statistics dict.
    """
    config = config or get_config()

    commands = load_commands(knowledge_dir)
    examples = generate_training_examples(commands)

    train, val, test = split_dataset(
        examples,
        train_ratio=config.training.train_split,
        val_ratio=config.training.val_split,
        test_ratio=config.training.test_split,
        seed=config.training.seed,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    save_jsonl(train, output_dir / "train.jsonl")
    save_jsonl(val, output_dir / "validation.jsonl")
    save_jsonl(test, output_dir / "test.jsonl")

    # Save command metadata
    cmd_meta = {cmd.id: cmd.model_dump() for cmd in commands}
    with open(output_dir / "command_metadata.json", "w") as f:
        json.dump(cmd_meta, f, indent=2)

    stats = {
        "total_commands": len(commands),
        "total_examples": len(examples),
        "train_examples": len(train),
        "val_examples": len(val),
        "test_examples": len(test),
        "technologies": len(set(cmd.technology for cmd in commands)),
    }

    with open(output_dir / "dataset_stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    logger.info("Dataset build complete: %s", stats)
    return stats
