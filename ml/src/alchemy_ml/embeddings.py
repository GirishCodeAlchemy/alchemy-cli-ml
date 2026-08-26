"""Embedding generation for AlchemyCLI AI.

Provides an abstract Embedder interface with a SentenceTransformer
implementation. Designed for future ONNX export.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np

from .config import get_config

logger = logging.getLogger(__name__)


class Embedder(ABC):
    """Abstract base class for text embedding models."""

    @abstractmethod
    def encode(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        """Encode texts into dense vectors.

        Args:
            texts: List of text strings to encode.
            batch_size: Batch size for encoding.

        Returns:
            numpy array of shape (len(texts), dimension).
        """
        ...

    @abstractmethod
    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text into a dense vector.

        Args:
            text: Text string to encode.

        Returns:
            numpy array of shape (dimension,).
        """
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name."""
        ...


class SentenceTransformerEmbedder(Embedder):
    """Embedder using sentence-transformers library."""

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        cache_dir: Path | None = None,
    ):
        """Initialize the SentenceTransformer embedder.

        Args:
            model_name: HuggingFace model name or local path.
            device: Device to use ('cpu', 'cuda', 'mps').
            cache_dir: Directory to cache downloaded models.
        """
        from sentence_transformers import SentenceTransformer

        config = get_config()
        self._model_name = model_name or config.embedding.model_name
        self._device = device or config.embedding.device
        self._batch_size = config.embedding.batch_size

        logger.info("Loading embedding model: %s (device=%s)", self._model_name, self._device)

        kwargs: dict = {"device": self._device}
        if cache_dir:
            kwargs["cache_folder"] = str(cache_dir)

        self._model = SentenceTransformer(self._model_name, **kwargs)
        # Support both old and new sentence-transformers API
        if hasattr(self._model, "get_embedding_dimension"):
            self._dimension = self._model.get_embedding_dimension()
        else:
            self._dimension = self._model.get_sentence_embedding_dimension()

        logger.info("Model loaded. Dimension: %d", self._dimension)

    def encode(self, texts: list[str], batch_size: int | None = None) -> np.ndarray:
        """Encode texts into dense vectors."""
        if not texts:
            return np.array([], dtype=np.float32).reshape(0, self._dimension)

        bs = batch_size or self._batch_size
        embeddings = self._model.encode(
            texts,
            batch_size=bs,
            show_progress_bar=len(texts) > 100,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return np.asarray(embeddings, dtype=np.float32)

    def encode_single(self, text: str) -> np.ndarray:
        """Encode a single text."""
        return self.encode([text])[0]

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name


class NumpyFallbackEmbedder(Embedder):
    """Simple TF-IDF + SVD fallback embedder when sentence-transformers unavailable.

    This provides basic functionality without requiring PyTorch or
    sentence-transformers. Quality will be lower but the system
    remains functional.
    """

    def __init__(self, dimension: int = 384):
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._dimension = dimension
        self._model_name = "tfidf-svd-fallback"
        self._vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),
            sublinear_tf=True,
        )
        self._svd = TruncatedSVD(n_components=dimension, random_state=42)
        self._fitted = False

    def fit(self, corpus: list[str]) -> None:
        """Fit the TF-IDF + SVD model on a corpus."""
        tfidf = self._vectorizer.fit_transform(corpus)
        # Adjust SVD components if corpus is small
        n_components = min(self._dimension, tfidf.shape[1], tfidf.shape[0])
        if n_components < self._dimension:
            from sklearn.decomposition import TruncatedSVD
            self._svd = TruncatedSVD(n_components=n_components, random_state=42)
            self._dimension = n_components
        self._svd.fit(tfidf)
        self._fitted = True
        logger.info("Fallback embedder fitted on %d documents", len(corpus))

    def encode(self, texts: list[str], batch_size: int = 64) -> np.ndarray:
        """Encode texts using TF-IDF + SVD."""
        if not self._fitted:
            raise RuntimeError("NumpyFallbackEmbedder must be fit() before encode()")
        if not texts:
            return np.array([], dtype=np.float32).reshape(0, self._dimension)

        tfidf = self._vectorizer.transform(texts)
        embeddings = self._svd.transform(tfidf).astype(np.float32)
        # L2 normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        return embeddings / norms

    def encode_single(self, text: str) -> np.ndarray:
        return self.encode([text])[0]

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name


# Factory function
_embedder: Embedder | None = None


def get_embedder(force_fallback: bool = False) -> Embedder:
    """Get or create the global embedder instance.

    Tries SentenceTransformer first, falls back to TF-IDF + SVD.
    """
    global _embedder
    if _embedder is not None:
        return _embedder

    if not force_fallback:
        try:
            _embedder = SentenceTransformerEmbedder()
            return _embedder
        except Exception as e:
            logger.warning("SentenceTransformer unavailable: %s. Using fallback.", e)

    _embedder = NumpyFallbackEmbedder()
    return _embedder


def reset_embedder() -> None:
    """Reset the global embedder (for testing)."""
    global _embedder
    _embedder = None
