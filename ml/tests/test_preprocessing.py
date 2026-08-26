"""Tests for query preprocessing."""

import pytest
from alchemy_ml.preprocessing import (
    compute_keyword_overlap,
    detect_all_technologies,
    detect_technology,
    expand_query,
    extract_keywords,
    is_ambiguous,
    normalize_query,
    redact_secrets,
)


class TestNormalizeQuery:
    def test_lowercase(self):
        assert normalize_query("HOW DO I RESTART") == "how do i restart"

    def test_whitespace(self):
        assert normalize_query("  how   do I  restart  ") == "how do i restart"

    def test_question_mark(self):
        assert normalize_query("how do I restart?") == "how do i restart"

    def test_typo_correction(self):
        assert "kubernetes" in normalize_query("restart kubernets deployment")

    def test_multiple_typos(self):
        result = normalize_query("dockr contaner logs")
        assert "docker" in result
        assert "container" in result


class TestDetectTechnology:
    def test_kubernetes(self):
        assert detect_technology("restart kubernetes deployment") == "kubernetes"

    def test_k8s(self):
        assert detect_technology("k8s pod logs") == "kubernetes"

    def test_kubectl(self):
        assert detect_technology("kubectl get pods") == "kubernetes"

    def test_docker(self):
        assert detect_technology("docker container logs") == "docker"

    def test_git(self):
        assert detect_technology("git commit undo") == "git"

    def test_python(self):
        assert detect_technology("python virtual environment") == "python"

    def test_rust(self):
        assert detect_technology("cargo build release") == "rust"

    def test_go(self):
        assert detect_technology("go test coverage") == "go"

    def test_kafka(self):
        assert detect_technology("kafka consumer lag") == "kafka"

    def test_terraform(self):
        assert detect_technology("terraform plan apply") == "terraform"

    def test_no_technology(self):
        assert detect_technology("hello world") is None

    def test_linux_from_port(self):
        assert detect_technology("what is using port 8080") == "linux"

    def test_linux_from_process(self):
        assert detect_technology("find process using memory") == "linux"


class TestDetectAllTechnologies:
    def test_single(self):
        assert detect_all_technologies("kubernetes pods") == ["kubernetes"]

    def test_multiple(self):
        result = detect_all_technologies("docker and kubernetes deployment")
        assert "docker" in result
        assert "kubernetes" in result


class TestExtractKeywords:
    def test_removes_stop_words(self):
        kw = extract_keywords("how do I restart a deployment")
        assert "how" not in kw
        assert "restart" in kw
        assert "deployment" in kw

    def test_short_words_removed(self):
        kw = extract_keywords("I go to a b c")
        assert "a" not in kw
        assert "b" not in kw


class TestIsAmbiguous:
    def test_pronoun(self):
        assert is_ambiguous("restart it") is True

    def test_single_verb(self):
        assert is_ambiguous("restart") is True

    def test_clear_query(self):
        assert is_ambiguous("restart kubernetes deployment") is False


class TestExpandQuery:
    def test_synonym_expansion(self):
        expanded = expand_query("delete the container")
        assert "remove" in expanded or "rm" in expanded

    def test_no_unnecessary_expansion(self):
        expanded = expand_query("kubernetes pods")
        assert "kubernetes" in expanded


class TestRedactSecrets:
    def test_redact_password(self):
        result = redact_secrets("password=mysecret123")
        assert "mysecret123" not in result
        assert "[REDACTED]" in result

    def test_redact_api_key(self):
        result = redact_secrets("api_key=sk-1234567890abcdefghijklmnopqrstuv")
        assert "sk-1234567890" not in result

    def test_no_redaction_needed(self):
        result = redact_secrets("how do I restart kubernetes")
        assert result == "how do I restart kubernetes"


class TestKeywordOverlap:
    def test_full_overlap(self):
        assert compute_keyword_overlap(["a", "b"], ["a", "b"]) == 1.0

    def test_no_overlap(self):
        assert compute_keyword_overlap(["a", "b"], ["c", "d"]) == 0.0

    def test_partial_overlap(self):
        score = compute_keyword_overlap(["a", "b", "c"], ["a", "b", "d"])
        assert 0.0 < score < 1.0

    def test_empty(self):
        assert compute_keyword_overlap([], ["a"]) == 0.0
