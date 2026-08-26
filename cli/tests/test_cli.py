"""Tests for the CLI."""

import json

import pytest
from click.testing import CliRunner
from alchemyai.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestCLIBasic:
    def test_version(self, runner):
        result = runner.invoke(main, ["version"])
        assert result.exit_code == 0
        assert "AlchemyCLI AI" in result.output

    def test_help(self, runner):
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "AlchemyCLI AI" in result.output

    def test_list(self, runner):
        result = runner.invoke(main, ["list"])
        assert result.exit_code == 0


class TestCLISearch:
    def test_json_output(self, runner):
        result = runner.invoke(main, ["--json", "list kubernetes pods"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "query" in data
        assert "results" in data

    def test_command_only(self, runner):
        result = runner.invoke(main, ["--cmd", "list kubernetes pods"])
        assert result.exit_code == 0
        # Output should be just the command (no rich formatting)
        output = result.output.strip()
        if output:  # May be empty if ML not loaded
            assert "\n" not in output or len(output.split("\n")) <= 2


class TestCLIModelInfo:
    def test_model_info(self, runner):
        result = runner.invoke(main, ["model", "info"])
        assert result.exit_code == 0
