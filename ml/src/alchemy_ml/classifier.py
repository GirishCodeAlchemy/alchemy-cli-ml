"""Intent classifier for AlchemyCLI AI.

Lightweight classifier that predicts technology and intent
from natural language queries using TF-IDF features.
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC

from .config import get_config
from .preprocessing import extract_keywords, normalize_query

logger = logging.getLogger(__name__)


class IntentClassifier:
    """Predicts technology and intent from natural language queries."""

    def __init__(self):
        config = get_config()
        self._config = config.classifier
        self._tech_pipeline: Pipeline | None = None
        self._intent_pipeline: Pipeline | None = None
        self._tech_encoder = LabelEncoder()
        self._intent_encoder = LabelEncoder()
        self._fitted = False

    def _build_pipeline(self) -> Pipeline:
        """Build a classification pipeline based on config."""
        vectorizer = TfidfVectorizer(
            max_features=self._config.tfidf_max_features,
            ngram_range=self._config.tfidf_ngram_range,
            sublinear_tf=True,
            strip_accents="unicode",
            analyzer="word",
            min_df=1,
            stop_words=None,  # Don't filter stop words on small test datasets
        )

        if self._config.model_type == "linear_svc":
            clf = LinearSVC(
                C=self._config.C,
                max_iter=self._config.max_iter,
                class_weight="balanced",
                random_state=42,
            )
        else:
            clf = LogisticRegression(
                C=self._config.C,
                max_iter=self._config.max_iter,
                class_weight="balanced",
                random_state=42,
                solver="lbfgs",
            )

        return Pipeline([("tfidf", vectorizer), ("clf", clf)])

    def fit(
        self,
        queries: list[str],
        technologies: list[str],
        intents: list[str],
    ) -> dict[str, float]:
        """Train the technology and intent classifiers.

        Args:
            queries: List of training queries.
            technologies: Technology label for each query.
            intents: Intent label for each query.

        Returns:
            Dict with training accuracy metrics.
        """
        if len(queries) != len(technologies) or len(queries) != len(intents):
            raise ValueError("queries, technologies, and intents must have same length")

        logger.info("Training classifiers on %d examples", len(queries))

        # Normalize queries
        normalized = [normalize_query(q) for q in queries]

        # Filter classes with too few samples
        tech_counts: dict[str, int] = {}
        intent_counts: dict[str, int] = {}
        for t, i in zip(technologies, intents):
            tech_counts[t] = tech_counts.get(t, 0) + 1
            intent_counts[i] = intent_counts.get(i, 0) + 1

        min_samples = self._config.min_samples_per_class
        valid_indices = [
            idx for idx, (t, i) in enumerate(zip(technologies, intents))
            if tech_counts[t] >= min_samples and intent_counts[i] >= min_samples
        ]

        if len(valid_indices) < len(queries):
            logger.warning(
                "Filtered %d examples with classes having < %d samples",
                len(queries) - len(valid_indices),
                min_samples,
            )

        filtered_queries = [normalized[i] for i in valid_indices]
        filtered_techs = [technologies[i] for i in valid_indices]
        filtered_intents = [intents[i] for i in valid_indices]

        # Encode labels
        tech_labels = self._tech_encoder.fit_transform(filtered_techs)
        intent_labels = self._intent_encoder.fit_transform(filtered_intents)

        # Train technology classifier
        tech_acc = 0.0
        try:
            pipeline = self._build_pipeline()
            pipeline.fit(filtered_queries, tech_labels)
            tech_acc = float(pipeline.score(filtered_queries, tech_labels))
            self._tech_pipeline = pipeline
        except (ValueError, Exception) as e:
            logger.warning("Failed to train technology classifier: %s", e)
            self._tech_pipeline = None

        # Train intent classifier
        intent_acc = 0.0
        try:
            pipeline = self._build_pipeline()
            pipeline.fit(filtered_queries, intent_labels)
            intent_acc = float(pipeline.score(filtered_queries, intent_labels))
            self._intent_pipeline = pipeline
        except (ValueError, Exception) as e:
            logger.warning("Failed to train intent classifier: %s", e)
            self._intent_pipeline = None

        self._fitted = True

        logger.info(
            "Training complete. Tech accuracy: %.3f, Intent accuracy: %.3f",
            tech_acc,
            intent_acc,
        )

        return {
            "technology_accuracy": tech_acc,
            "intent_accuracy": intent_acc,
            "num_technologies": len(self._tech_encoder.classes_),
            "num_intents": len(self._intent_encoder.classes_),
            "num_examples": len(filtered_queries),
        }

    def predict_technology(self, query: str) -> tuple[str, float]:
        """Predict the technology for a query.

        Returns:
            Tuple of (technology, confidence).
        """
        if not self._fitted or self._tech_pipeline is None:
            return ("", 0.0)

        normalized = normalize_query(query)
        label = self._tech_pipeline.predict([normalized])[0]
        technology = str(self._tech_encoder.inverse_transform([label])[0])

        # Get confidence
        confidence = self._get_confidence(self._tech_pipeline, normalized)

        return (technology, confidence)

    def predict_intent(self, query: str) -> tuple[str, float]:
        """Predict the intent for a query.

        Returns:
            Tuple of (intent, confidence).
        """
        if not self._fitted or self._intent_pipeline is None:
            return ("", 0.0)

        normalized = normalize_query(query)
        label = self._intent_pipeline.predict([normalized])[0]
        intent = str(self._intent_encoder.inverse_transform([label])[0])

        confidence = self._get_confidence(self._intent_pipeline, normalized)

        return (intent, confidence)

    def predict(self, query: str) -> dict[str, Any]:
        """Predict both technology and intent.

        Returns:
            Dict with technology, intent, and confidences.
        """
        tech, tech_conf = self.predict_technology(query)
        intent, intent_conf = self.predict_intent(query)

        return {
            "technology": tech,
            "technology_confidence": tech_conf,
            "intent": intent,
            "intent_confidence": intent_conf,
        }

    def predict_top_k(self, query: str, k: int = 3) -> dict[str, list[tuple[str, float]]]:
        """Predict top-k technologies and intents.

        Returns:
            Dict with 'technologies' and 'intents' lists.
        """
        result: dict[str, list[tuple[str, float]]] = {
            "technologies": [],
            "intents": [],
        }

        if not self._fitted:
            return result

        normalized = normalize_query(query)

        # Technology predictions
        if self._tech_pipeline is not None:
            probs = self._get_probabilities(self._tech_pipeline, normalized)
            if probs is not None:
                top_idx = np.argsort(probs)[::-1][:k]
                for idx in top_idx:
                    label = str(self._tech_encoder.inverse_transform([idx])[0])
                    result["technologies"].append((label, float(probs[idx])))

        # Intent predictions
        if self._intent_pipeline is not None:
            probs = self._get_probabilities(self._intent_pipeline, normalized)
            if probs is not None:
                top_idx = np.argsort(probs)[::-1][:k]
                for idx in top_idx:
                    label = str(self._intent_encoder.inverse_transform([idx])[0])
                    result["intents"].append((label, float(probs[idx])))

        return result

    def _get_confidence(self, pipeline: Pipeline, text: str) -> float:
        """Get prediction confidence from a pipeline."""
        probs = self._get_probabilities(pipeline, text)
        if probs is not None:
            return float(np.max(probs))
        return 0.5  # Default for SVM without probability

    def _get_probabilities(self, pipeline: Pipeline, text: str) -> np.ndarray | None:
        """Get class probabilities from a pipeline."""
        clf = pipeline.named_steps["clf"]
        tfidf = pipeline.named_steps["tfidf"]
        features = tfidf.transform([text])

        if hasattr(clf, "predict_proba"):
            return clf.predict_proba(features)[0]
        elif hasattr(clf, "decision_function"):
            decisions = clf.decision_function(features)[0]
            # Convert decision function to pseudo-probabilities via softmax
            if decisions.ndim == 0:
                return None
            exp_d = np.exp(decisions - np.max(decisions))
            return exp_d / exp_d.sum()
        return None

    def save(self, path: Path) -> None:
        """Save classifier to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        if self._tech_pipeline is not None:
            with open(path / "tech_pipeline.pkl", "wb") as f:
                pickle.dump(self._tech_pipeline, f)

        if self._intent_pipeline is not None:
            with open(path / "intent_pipeline.pkl", "wb") as f:
                pickle.dump(self._intent_pipeline, f)

        with open(path / "tech_encoder.pkl", "wb") as f:
            pickle.dump(self._tech_encoder, f)

        with open(path / "intent_encoder.pkl", "wb") as f:
            pickle.dump(self._intent_encoder, f)

        # Save metadata
        meta = {
            "fitted": self._fitted,
            "model_type": self._config.model_type,
            "num_technologies": len(self._tech_encoder.classes_) if self._fitted else 0,
            "num_intents": len(self._intent_encoder.classes_) if self._fitted else 0,
            "technologies": list(self._tech_encoder.classes_) if self._fitted else [],
            "intents": list(self._intent_encoder.classes_) if self._fitted else [],
        }
        with open(path / "classifier_meta.json", "w") as f:
            json.dump(meta, f, indent=2)

        logger.info("Saved classifier to %s", path)

    def load(self, path: Path) -> None:
        """Load classifier from disk."""
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Classifier not found: {path}")

        tech_path = path / "tech_pipeline.pkl"
        intent_path = path / "intent_pipeline.pkl"
        tech_enc_path = path / "tech_encoder.pkl"
        intent_enc_path = path / "intent_encoder.pkl"

        if tech_path.exists():
            with open(tech_path, "rb") as f:
                self._tech_pipeline = pickle.load(f)

        if intent_path.exists():
            with open(intent_path, "rb") as f:
                self._intent_pipeline = pickle.load(f)

        if tech_enc_path.exists():
            with open(tech_enc_path, "rb") as f:
                self._tech_encoder = pickle.load(f)

        if intent_enc_path.exists():
            with open(intent_enc_path, "rb") as f:
                self._intent_encoder = pickle.load(f)

        self._fitted = True
        logger.info("Loaded classifier from %s", path)

    @property
    def is_fitted(self) -> bool:
        return self._fitted

    @property
    def technologies(self) -> list[str]:
        if self._fitted:
            return list(self._tech_encoder.classes_)
        return []

    @property
    def intents(self) -> list[str]:
        if self._fitted:
            return list(self._intent_encoder.classes_)
        return []
