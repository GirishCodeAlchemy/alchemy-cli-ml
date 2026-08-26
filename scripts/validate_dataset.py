#!/usr/bin/env python3
"""Validate all knowledge base YAML files against the command schema."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REQUIRED_FIELDS = {"id", "technology", "category", "name", "intent", "command", "description", "risk"}
VALID_RISKS = {"safe", "warning", "dangerous"}
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return [f"{path}: YAML parse error: {e}"]

    if not isinstance(data, list):
        return [f"{path}: expected list, got {type(data).__name__}"]

    ids_seen: set[str] = set()
    for i, entry in enumerate(data):
        prefix = f"{path}[{i}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix}: expected dict, got {type(entry).__name__}")
            continue

        # Check required fields
        missing = REQUIRED_FIELDS - set(entry.keys())
        if missing:
            errors.append(f"{prefix} ({entry.get('id', '?')}): missing fields: {missing}")

        # Check risk value
        risk = entry.get("risk", "")
        if risk and risk not in VALID_RISKS:
            errors.append(f"{prefix} ({entry.get('id', '?')}): invalid risk: {risk}")

        # Check duplicate IDs
        cmd_id = entry.get("id", "")
        if cmd_id in ids_seen:
            errors.append(f"{prefix}: duplicate id: {cmd_id}")
        ids_seen.add(cmd_id)

        # Check command is not empty
        if not entry.get("command", "").strip():
            errors.append(f"{prefix} ({cmd_id}): empty command")

        # Check description is not empty
        if not entry.get("description", "").strip():
            errors.append(f"{prefix} ({cmd_id}): empty description")

    return errors


def main() -> int:
    knowledge_dir = PROJECT_ROOT / "knowledge"
    if not knowledge_dir.exists():
        print(f"ERROR: Knowledge directory not found: {knowledge_dir}")
        return 1

    all_errors: list[str] = []
    total_commands = 0
    total_files = 0

    for yaml_file in sorted(knowledge_dir.rglob("*.yaml")):
        total_files += 1
        errors = validate_file(yaml_file)
        all_errors.extend(errors)

        with open(yaml_file) as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            total_commands += len(data)

    print(f"Validated {total_files} files, {total_commands} commands")

    if all_errors:
        print(f"\n{len(all_errors)} errors found:\n")
        for err in all_errors:
            print(f"  ✗ {err}")
        return 1

    print("✓ All commands valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
