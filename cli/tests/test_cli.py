"""Tests for the CLI."""

import json
import os

import pytest
from click.testing import CliRunner
from alchemyai.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIBasic:
    def test_version_flag(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "AlchemyCLI AI" in result.output

    def test_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "AlchemyCLI AI" in result.output

    def test_list(self, runner):
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0

    def test_version_subcommand(self, runner):
        result = runner.invoke(main, ["version"])
        assert result.exit_code == 0
        assert "AlchemyCLI AI" in result.output


class TestCLISearch:
    def test_json_output(self, runner):
        result = runner.invoke(main, ["--json", "--mode", "keyword", "list kubernetes pods"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "query" in data
        assert "results" in data

    def test_command_only(self, runner):
        result = runner.invoke(main, ["--cmd", "--mode", "keyword", "list kubernetes pods"])
        assert result.exit_code == 0
        output = result.output.strip()
        if output:
            # Should be a single command line, no rich formatting
            lines = [l for l in output.split("\n") if l.strip()]
            assert len(lines) <= 2


class TestCLIModelInfo:
    def test_model_info(self, runner):
        result = runner.invoke(main, ["model", "info"])
        assert result.exit_code == 0
