"""Tests for vector store retrieval."""

import numpy as np
import pytest
from alchemy_ml.retrieval import NumpyStore, create_vector_store


class TestNumpyStore:
    def test_add_and_search(self):
        store = NumpyStore()
        embeddings = np.random.randn(5, 384).astype(np.float32)
        # Normalize
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        metadata = [{"command_id": f"cmd-{i}"} for i in range(5)]

        store.add(embeddings, metadata)
        assert store.size() == 5

        results = store.search(embeddings[0], top_k=3)
        assert len(results) == 3
        # First result should be the query itself (highest similarity)
        assert results[0][0]["command_id"] == "cmd-0"
        assert results[0][1] > 0.99  # Self-similarity

    def test_empty_search(self):
        store = NumpyStore()
        embedding = np.random.randn(384).astype(np.float32)
        results = store.search(embedding)
        assert results == []

    def test_clear(self):
        store = NumpyStore()
        embeddings = np.random.randn(3, 384).astype(np.float32)
        store.add(embeddings, [{"id": i} for i in range(3)])
        assert store.size() == 3
        store.clear()
        assert store.size() == 0

    def test_save_and_load(self, tmp_path):
        store = NumpyStore()
        embeddings = np.random.randn(5, 384).astype(np.float32)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        metadata = [{"command_id": f"cmd-{i}"} for i in range(5)]
        store.add(embeddings, metadata)

        path = tmp_path / "test_index.faiss"
        store.save(path)

        store2 = NumpyStore()
        store2.load(path)
        assert store2.size() == 5

        results = store2.search(embeddings[0], top_k=1)
        assert results[0][0]["command_id"] == "cmd-0"


class TestCreateVectorStore:
    def test_creates_store(self):
        store = create_vector_store(use_faiss=False)
        assert isinstance(store, NumpyStore)
