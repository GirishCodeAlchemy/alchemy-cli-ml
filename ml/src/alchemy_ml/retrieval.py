"""Vector retrieval for AlchemyCLI AI.

Abstract VectorStore interface with FAISS implementation.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import numpy as np

from .config import get_config

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """Abstract vector store interface."""

    @abstractmethod
    def add(self, embeddings: np.ndarray, metadata: list[dict[str, Any]]) -> None:
        """Add embeddings with associated metadata.

        Args:
            embeddings: numpy array of shape (n, dimension).
            metadata: list of metadata dicts, one per embedding.
        """
        ...

    @abstractmethod
    def search(self, embedding: np.ndarray, top_k: int = 10) -> list[tuple[dict[str, Any], float]]:
        """Search for nearest neighbors.

        Args:
            embedding: Query vector of shape (dimension,).
            top_k: Number of results to return.

        Returns:
            List of (metadata, similarity_score) tuples, sorted by score descending.
        """
        ...

    @abstractmethod
    def save(self, path: Path) -> None:
        """Persist the index to disk."""
        ...

    @abstractmethod
    def load(self, path: Path) -> None:
        """Load the index from disk."""
        ...

    @abstractmethod
    def size(self) -> int:
        """Return the number of vectors in the store."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all vectors."""
        ...


class FAISSStore(VectorStore):
    """FAISS-based vector store for local similarity search."""

    def __init__(self, dimension: int | None = None, index_type: str = "flat"):
        """Initialize FAISS store.

        Args:
            dimension: Embedding dimension. Set on first add() if None.
            index_type: FAISS index type ('flat' or 'ivf').
        """
        self._dimension = dimension
        self._index_type = index_type
        self._index = None
        self._metadata: list[dict[str, Any]] = []
        self._faiss = None

    def _ensure_faiss(self):
        """Lazy import of faiss."""
        if self._faiss is None:
            import faiss
            self._faiss = faiss

    def _create_index(self, dimension: int) -> Any:
        """Create a FAISS index of the configured type."""
        self._ensure_faiss()
        if self._index_type == "ivf":
            quantizer = self._faiss.IndexFlatIP(dimension)
            # IVF with 100 centroids — needs training
            index = self._faiss.IndexIVFFlat(quantizer, dimension, min(100, max(1, len(self._metadata) // 10)))
            return index
        # Default: flat inner product (for normalized vectors, IP == cosine)
        return self._faiss.IndexFlatIP(dimension)

    def add(self, embeddings: np.ndarray, metadata: list[dict[str, Any]]) -> None:
        """Add embeddings to the FAISS index."""
        if len(embeddings) == 0:
            return

        if len(embeddings) != len(metadata):
            raise ValueError(
                f"Embedding count ({len(embeddings)}) != metadata count ({len(metadata)})"
            )

        embeddings = np.asarray(embeddings, dtype=np.float32)

        if self._dimension is None:
            self._dimension = embeddings.shape[1]

        if self._index is None:
            self._index = self._create_index(self._dimension)

        # For IVF indices, train if not yet trained
        self._ensure_faiss()
        if hasattr(self._index, "is_trained") and not self._index.is_trained:
            self._index.train(embeddings)

        self._index.add(embeddings)
        self._metadata.extend(metadata)

        logger.info("Added %d vectors. Total: %d", len(embeddings), self._index.ntotal)

    def search(self, embedding: np.ndarray, top_k: int = 10) -> list[tuple[dict[str, Any], float]]:
        """Search for nearest neighbors using FAISS."""
        if self._index is None or self._index.ntotal == 0:
            return []

        embedding = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
        k = min(top_k, self._index.ntotal)

        # Set nprobe for IVF indices
        if hasattr(self._index, "nprobe"):
            config = get_config()
            self._index.nprobe = config.retrieval.faiss_nprobe

        scores, indices = self._index.search(embedding, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self._metadata):
                continue
            results.append((self._metadata[idx], float(score)))

        return results

    def save(self, path: Path) -> None:
        """Save index and metadata to disk."""
        self._ensure_faiss()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if self._index is not None:
            self._faiss.write_index(self._index, str(path))

        metadata_path = path.with_suffix(".meta.json")
        with open(metadata_path, "w") as f:
            json.dump(
                {
                    "dimension": self._dimension,
                    "index_type": self._index_type,
                    "count": len(self._metadata),
                    "metadata": self._metadata,
                },
                f,
                indent=2,
            )

        logger.info("Saved FAISS index to %s (%d vectors)", path, len(self._metadata))

    def load(self, path: Path) -> None:
        """Load index and metadata from disk."""
        self._ensure_faiss()
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"FAISS index not found: {path}")

        self._index = self._faiss.read_index(str(path))

        metadata_path = path.with_suffix(".meta.json")
        if metadata_path.exists():
            with open(metadata_path) as f:
                data = json.load(f)
            self._metadata = data.get("metadata", [])
            self._dimension = data.get("dimension")
            self._index_type = data.get("index_type", "flat")
        else:
            logger.warning("No metadata file found for FAISS index")
            self._metadata = []

        logger.info("Loaded FAISS index from %s (%d vectors)", path, self._index.ntotal)

    def size(self) -> int:
        return self._index.ntotal if self._index else 0

    def clear(self) -> None:
        self._index = None
        self._metadata = []


class NumpyStore(VectorStore):
    """Pure numpy fallback vector store when FAISS is unavailable."""

    def __init__(self):
        self._embeddings: np.ndarray | None = None
        self._metadata: list[dict[str, Any]] = []

    def add(self, embeddings: np.ndarray, metadata: list[dict[str, Any]]) -> None:
        embeddings = np.asarray(embeddings, dtype=np.float32)
        if self._embeddings is None:
            self._embeddings = embeddings
        else:
            self._embeddings = np.vstack([self._embeddings, embeddings])
        self._metadata.extend(metadata)

    def search(self, embedding: np.ndarray, top_k: int = 10) -> list[tuple[dict[str, Any], float]]:
        if self._embeddings is None or len(self._embeddings) == 0:
            return []

        embedding = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
        # Cosine similarity (vectors are normalized)
        scores = (self._embeddings @ embedding.T).flatten()
        k = min(top_k, len(scores))
        top_indices = np.argsort(scores)[::-1][:k]

        return [(self._metadata[i], float(scores[i])) for i in top_indices]

    def save(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if self._embeddings is not None:
            np.save(str(path.with_suffix(".npy")), self._embeddings)
        meta_path = path.with_suffix(".meta.json")
        with open(meta_path, "w") as f:
            json.dump({"count": len(self._metadata), "metadata": self._metadata}, f, indent=2)

    def load(self, path: Path) -> None:
        path = Path(path)
        npy_path = path.with_suffix(".npy")
        if npy_path.exists():
            self._embeddings = np.load(str(npy_path))
        meta_path = path.with_suffix(".meta.json")
        if meta_path.exists():
            with open(meta_path) as f:
                data = json.load(f)
            self._metadata = data.get("metadata", [])

    def size(self) -> int:
        return len(self._metadata)

    def clear(self) -> None:
        self._embeddings = None
        self._metadata = []


def create_vector_store(
    dimension: int | None = None,
    use_faiss: bool = True,
) -> VectorStore:
    """Create a vector store instance.

    Tries FAISS first, falls back to numpy.
    """
    if use_faiss:
        try:
            import faiss  # noqa: F401
            config = get_config()
            return FAISSStore(dimension=dimension, index_type=config.retrieval.faiss_index_type)
        except ImportError:
            logger.warning("FAISS not available, using numpy fallback.")

    return NumpyStore()
