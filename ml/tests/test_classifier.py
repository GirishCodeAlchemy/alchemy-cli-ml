"""Tests for intent classifier."""

import pytest
from alchemy_ml.classifier import IntentClassifier


class TestIntentClassifier:
    def setup_method(self):
        self.queries = [
            "restart kubernetes deployment",
            "list kubernetes pods",
            "get kubernetes services",
            "view kubernetes logs",
            "scale kubernetes deployment",
            "docker container logs",
            "docker run container",
            "docker build image",
            "docker stop container",
            "docker list images",
            "git commit changes",
            "git push to remote",
            "git create branch",
            "git merge branches",
            "git stash changes",
        ]
        self.technologies = [
            "kubernetes", "kubernetes", "kubernetes", "kubernetes", "kubernetes",
            "docker", "docker", "docker", "docker", "docker",
            "git", "git", "git", "git", "git",
        ]
        self.intents = [
            "restart_deployment", "list_pods", "get_services", "view_logs", "scale_deployment",
            "container_logs", "run_container", "build_image", "stop_container", "list_images",
            "commit", "push", "create_branch", "merge", "stash",
        ]

    def test_fit(self):
        clf = IntentClassifier()
        metrics = clf.fit(self.queries, self.technologies, self.intents)
        assert clf.is_fitted
        assert metrics["technology_accuracy"] > 0.5
        assert metrics["num_technologies"] == 3

    def test_predict_technology(self):
        clf = IntentClassifier()
        clf.fit(self.queries, self.technologies, self.intents)
        tech, conf = clf.predict_technology("restart the kubernetes deployment")
        assert tech == "kubernetes"
        assert conf > 0.0

    def test_predict_intent(self):
        clf = IntentClassifier()
        clf.fit(self.queries, self.technologies, self.intents)
        intent, conf = clf.predict_intent("docker container logs")
        assert len(intent) > 0
        assert conf > 0.0

    def test_predict(self):
        clf = IntentClassifier()
        clf.fit(self.queries, self.technologies, self.intents)
        result = clf.predict("git push to remote")
        assert "technology" in result
        assert "intent" in result

    def test_not_fitted(self):
        clf = IntentClassifier()
        tech, conf = clf.predict_technology("test")
        assert tech == ""
        assert conf == 0.0

    def test_save_load(self, tmp_path):
        clf = IntentClassifier()
        clf.fit(self.queries, self.technologies, self.intents)

        clf.save(tmp_path / "clf")

        clf2 = IntentClassifier()
        clf2.load(tmp_path / "clf")
        assert clf2.is_fitted

        tech, _ = clf2.predict_technology("kubernetes pods")
        assert tech == "kubernetes"
