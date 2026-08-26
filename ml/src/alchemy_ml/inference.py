"""Main inference engine for AlchemyCLI AI.

Orchestrates the full query pipeline: preprocessing → embedding →
retrieval → classification → ranking → safety → response.
"""

from __future__ import annotations

import json
import logging
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any

import yaml

from .classifier import IntentClassifier
from .config import Config, get_config
from .embeddings import Embedder, NumpyFallbackEmbedder, get_embedder, reset_embedder
from .models import (
    AskResponse,
    ClarificationOption,
    ClarificationRequest,
    Command,
    ModelInfo,
    RiskLevel,
    SearchResult,
)
from .preprocessing import (
    detect_technology,
    expand_query,
    extract_keywords,
    is_ambiguous,
    normalize_query,
    redact_secrets,
)
from .ranking import HybridRanker, compute_confidence_label
from .retrieval import VectorStore, create_vector_store
from .safety import classify_risk, validate_no_execution

logger = logging.getLogger(__name__)


class LRUCache:
    """Simple LRU cache for query embeddings."""

    def __init__(self, max_size: int = 1024):
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, key: str, value: Any) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self._max_size:
                self._cache.popitem(last=False)
        self._cache[key] = value

    def clear(self) -> None:
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)


class InferenceEngine:
    """Main inference engine that ties all ML components together."""

    def __init__(self, config: Config | None = None):
        self._config = config or get_config()
        self._commands: dict[str, Command] = {}
        self._embedder: Embedder | None = None
        self._vector_store: VectorStore | None = None
        self._classifier = IntentClassifier()
        self._ranker = HybridRanker()
        self._cache = LRUCache(max_size=self._config.cache.max_size)
        self._loaded = False
        self._context: list[dict[str, str]] = []

    # ── Loading ──────────────────────────────────────────────

    def load_commands(self, knowledge_dir: Path | None = None) -> int:
        """Load commands from YAML knowledge base files.

        Args:
            knowledge_dir: Path to knowledge directory. Defaults to config.

        Returns:
            Number of commands loaded.
        """
        knowledge_dir = knowledge_dir or self._config.knowledge_dir
        if not knowledge_dir.exists():
            logger.warning("Knowledge directory not found: %s", knowledge_dir)
            return 0

        count = 0
        for yaml_file in sorted(knowledge_dir.rglob("*.yaml")):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)

                if not isinstance(data, list):
                    logger.warning("Skipping %s: expected list, got %s", yaml_file, type(data))
                    continue

                for entry in data:
                    if not isinstance(entry, dict):
                        continue
                    try:
                        cmd = Command(**entry)
                        self._commands[cmd.id] = cmd
                        count += 1
                    except Exception as e:
                        logger.warning("Invalid command in %s: %s", yaml_file, e)

            except Exception as e:
                logger.error("Error loading %s: %s", yaml_file, e)

        # Also load user custom commands
        user_dir = self._config.user_commands_dir
        if user_dir.exists():
            for yaml_file in sorted(user_dir.rglob("*.yaml")):
                try:
                    with open(yaml_file) as f:
                        data = yaml.safe_load(f)
                    if isinstance(data, list):
                        for entry in data:
                            if isinstance(entry, dict):
                                try:
                                    cmd = Command(**entry)
                                    self._commands[cmd.id] = cmd
                                    count += 1
                                except Exception:
                                    pass
                except Exception:
                    pass

        logger.info("Loaded %d commands from knowledge base", count)
        return count

    def build_index(self) -> None:
        """Build the FAISS index from loaded commands.

        Generates embeddings for all commands and adds them to
        the vector store.
        """
        if not self._commands:
            raise RuntimeError("No commands loaded. Call load_commands() first.")

        # Initialize embedder
        self._embedder = get_embedder()

        # If using fallback embedder, fit it first
        if isinstance(self._embedder, NumpyFallbackEmbedder):
            corpus = [cmd.searchable_text for cmd in self._commands.values()]
            self._embedder.fit(corpus)

        # Generate embeddings for all commands
        command_list = list(self._commands.values())
        texts = [cmd.searchable_text for cmd in command_list]

        logger.info("Generating embeddings for %d commands...", len(texts))
        embeddings = self._embedder.encode(texts)

        # Build vector store
        self._vector_store = create_vector_store(dimension=self._embedder.dimension)
        metadata = [{"command_id": cmd.id} for cmd in command_list]
        self._vector_store.add(embeddings, metadata)

        self._loaded = True
        logger.info("Index built with %d vectors", self._vector_store.size())

    def save_index(self, path: Path | None = None) -> None:
        """Save the FAISS index to disk."""
        path = path or self._config.faiss_index_path
        if self._vector_store:
            self._vector_store.save(path)
            logger.info("Index saved to %s", path)

    def load_index(self, path: Path | None = None) -> None:
        """Load a pre-built FAISS index from disk."""
        path = path or self._config.faiss_index_path
        if not path.exists():
            raise FileNotFoundError(f"Index not found: {path}")

        self._vector_store = create_vector_store()
        self._vector_store.load(path)
        self._loaded = True
        logger.info("Index loaded from %s", path)

    def load_classifier(self, path: Path | None = None) -> None:
        """Load a trained intent classifier."""
        path = path or self._config.classifier_path
        if path.exists():
            self._classifier.load(path)
            logger.info("Classifier loaded from %s", path)
        else:
            logger.info("No classifier found at %s, skipping", path)

    def initialize(self) -> None:
        """Full initialization: load commands, build/load index, load classifier."""
        self.load_commands()

        # Try loading pre-built index first
        try:
            self.load_index()
            self._embedder = get_embedder()
        except FileNotFoundError:
            logger.info("No pre-built index found, building from scratch...")
            self.build_index()
            self.save_index()

        # Try loading classifier
        try:
            self.load_classifier()
        except Exception as e:
            logger.info("Classifier not available: %s", e)

    # ── Query Pipeline ───────────────────────────────────────

    def ask(
        self,
        query: str,
        top_k: int | None = None,
        mode: str = "hybrid",
        explain: bool = False,
        debug: bool = False,
    ) -> AskResponse:
        """Process a natural language query and return matching commands.

        This is the main entry point for the query pipeline:
        1. Sanitize & redact secrets
        2. Normalize query
        3. Check for ambiguity
        4. Detect technology
        5. Classify intent
        6. Generate query embedding
        7. Retrieve candidates from FAISS
        8. Apply hybrid ranking
        9. Filter by confidence threshold
        10. Return results

        Args:
            query: Natural language question.
            top_k: Number of results to return.
            mode: Search mode ('semantic', 'keyword', 'hybrid').
            explain: Include explanation in results.
            debug: Include debug info in response.

        Returns:
            AskResponse with ranked results.
        """
        start_time = time.monotonic()
        top_k = top_k or self._config.retrieval.top_k
        debug_info: dict[str, Any] = {} if debug else {}

        # Safety: validate input
        if not validate_no_execution(query):
            return AskResponse(
                query=query,
                results=[],
                clarification=ClarificationRequest(
                    message="Query contains potentially unsafe patterns. Please rephrase.",
                    options=[],
                ),
            )

        # Redact secrets
        query = redact_secrets(query)

        # Normalize
        normalized = normalize_query(query)
        if debug:
            debug_info["normalized_query"] = normalized

        # Check ambiguity
        if is_ambiguous(normalized):
            return self._handle_ambiguous(query, normalized)

        # Use context for follow-up queries
        resolved = self._resolve_context(normalized)
        if resolved != normalized:
            normalized = resolved
            if debug:
                debug_info["context_resolved"] = normalized

        # Detect technology
        detected_tech = detect_technology(normalized)
        if debug:
            debug_info["detected_technology"] = detected_tech

        # Classify intent
        detected_intent = None
        if self._classifier.is_fitted:
            prediction = self._classifier.predict(normalized)
            detected_intent = prediction.get("intent")
            if debug:
                debug_info["classifier_prediction"] = prediction

        # Route by mode
        if mode == "keyword":
            results = self._keyword_search(normalized, top_k, detected_tech, detected_intent)
        elif mode == "semantic":
            results = self._semantic_search(normalized, top_k, detected_tech, detected_intent)
        else:
            results = self._hybrid_search(normalized, top_k, detected_tech, detected_intent)

        # Filter by confidence
        config = self._config
        filtered = [r for r in results if r.confidence >= config.confidence_threshold]

        # If no confident results, show low-confidence message
        if not filtered and results:
            return AskResponse(
                query=query,
                results=results[:3],
                clarification=ClarificationRequest(
                    message="I couldn't confidently identify the command. These are my best guesses:",
                    options=[],
                ),
            )

        # Remove explanation if not requested
        if not explain:
            for r in filtered:
                r.explanation = None

        # Store context
        self._add_context(query, detected_tech)

        elapsed = time.monotonic() - start_time
        if debug:
            debug_info["elapsed_ms"] = round(elapsed * 1000, 1)
            debug_info["candidates_before_filter"] = len(results)
            debug_info["results_after_filter"] = len(filtered)

        return AskResponse(
            query=query,
            results=filtered,
            debug=debug_info if debug else None,
        )

    def _semantic_search(
        self,
        query: str,
        top_k: int,
        detected_tech: str | None,
        detected_intent: str | None,
    ) -> list[SearchResult]:
        """Pure semantic search using embeddings."""
        if not self._embedder or not self._vector_store:
            return self._keyword_search(query, top_k, detected_tech, detected_intent)

        # Check cache
        cached = self._cache.get(f"emb:{query}")
        if cached is not None:
            embedding = cached
        else:
            embedding = self._embedder.encode_single(query)
            self._cache.put(f"emb:{query}", embedding)

        # Search vector store
        raw_results = self._vector_store.search(embedding, top_k=top_k * 2)

        # Map to commands
        candidates: list[tuple[Command, float]] = []
        for meta, score in raw_results:
            cmd_id = meta.get("command_id", "")
            if cmd_id in self._commands:
                candidates.append((self._commands[cmd_id], score))

        return self._ranker.rank(candidates, query, detected_tech, detected_intent, top_k)

    def _keyword_search(
        self,
        query: str,
        top_k: int,
        detected_tech: str | None,
        detected_intent: str | None,
    ) -> list[SearchResult]:
        """Keyword-based search as fallback."""
        keywords = extract_keywords(query)
        expanded = expand_query(query)
        expanded_keywords = extract_keywords(expanded)
        all_keywords = list(set(keywords + expanded_keywords))

        if not all_keywords:
            return []

        scored: list[tuple[Command, float]] = []
        for cmd in self._commands.values():
            cmd_text = cmd.searchable_text.lower()
            cmd_keywords = extract_keywords(cmd_text)

            # Score based on keyword overlap
            score = 0.0
            matched = 0
            for kw in all_keywords:
                if kw in cmd_text:
                    matched += 1
                elif any(kw in ck for ck in cmd_keywords):
                    matched += 0.5

            if matched > 0:
                score = matched / len(all_keywords)
                # Technology boost
                if detected_tech and cmd.technology == detected_tech:
                    score = min(1.0, score + 0.15)
                scored.append((cmd, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return self._ranker.rank(scored[:top_k * 2], query, detected_tech, detected_intent, top_k)

    def _hybrid_search(
        self,
        query: str,
        top_k: int,
        detected_tech: str | None,
        detected_intent: str | None,
    ) -> list[SearchResult]:
        """Hybrid search combining semantic and keyword retrieval."""
        semantic_results = self._semantic_search(query, top_k * 2, detected_tech, detected_intent)
        keyword_results = self._keyword_search(query, top_k * 2, detected_tech, detected_intent)

        # Merge by command_id, taking the higher confidence
        merged: dict[str, SearchResult] = {}
        for r in semantic_results + keyword_results:
            if r.command_id not in merged or r.confidence > merged[r.command_id].confidence:
                merged[r.command_id] = r

        # Sort by confidence
        results = sorted(merged.values(), key=lambda r: r.confidence, reverse=True)
        return results[:top_k]

    def _handle_ambiguous(self, query: str, normalized: str) -> AskResponse:
        """Handle ambiguous queries by asking for clarification."""
        # Detect possible technologies
        options: list[ClarificationOption] = []

        # Common ambiguous patterns
        verbs = {"restart", "delete", "remove", "stop", "start", "create", "show", "list"}
        words = normalized.split()
        verb = next((w for w in words if w in verbs), words[0] if words else "")

        tech_options = [
            ("Kubernetes deployment", "kubernetes", f"{verb} kubernetes deployment"),
            ("Docker container", "docker", f"{verb} docker container"),
            ("Linux service", "linux", f"{verb} linux service"),
            ("Git repository", "git", f"{verb} git"),
        ]

        for label, tech, refined_query in tech_options:
            options.append(ClarificationOption(
                label=label,
                technology=tech,
                query=refined_query,
            ))

        return AskResponse(
            query=query,
            results=[],
            clarification=ClarificationRequest(
                message=f"What would you like to {verb}?",
                options=options,
            ),
        )

    # ── Context ──────────────────────────────────────────────

    def _add_context(self, query: str, technology: str | None) -> None:
        """Store query in local conversation context."""
        self._context.append({
            "query": query,
            "technology": technology or "",
            "timestamp": str(time.time()),
        })
        # Keep only recent context
        max_ctx = self._config.context.max_history
        if len(self._context) > max_ctx:
            self._context = self._context[-max_ctx:]

    def _resolve_context(self, query: str) -> str:
        """Resolve pronouns using recent context."""
        if not self._context:
            return query

        pronouns = {"it", "this", "that", "them", "those", "these"}
        words = query.split()

        has_pronoun = any(w in pronouns for w in words)
        if not has_pronoun:
            return query

        # Look at last context entry for technology
        last = self._context[-1]
        last_tech = last.get("technology", "")

        if last_tech:
            # Replace pronoun with technology context
            resolved = query
            for pronoun in pronouns:
                if pronoun in words:
                    resolved = resolved.replace(pronoun, last_tech, 1)
                    break
            return resolved

        return query

    def clear_context(self) -> None:
        """Clear conversation context."""
        self._context.clear()

    # ── Direct Access ────────────────────────────────────────

    def get_command(self, command_id: str) -> Command | None:
        """Get a command by ID."""
        return self._commands.get(command_id)

    def get_commands_by_technology(self, technology: str) -> list[Command]:
        """Get all commands for a technology."""
        return [
            cmd for cmd in self._commands.values()
            if cmd.technology.lower() == technology.lower()
        ]

    def get_all_technologies(self) -> list[str]:
        """Get sorted list of all technologies."""
        return sorted(set(cmd.technology for cmd in self._commands.values()))

    def get_all_categories(self) -> dict[str, list[str]]:
        """Get all categories grouped by technology."""
        cats: dict[str, set[str]] = {}
        for cmd in self._commands.values():
            cats.setdefault(cmd.technology, set()).add(cmd.category)
        return {k: sorted(v) for k, v in sorted(cats.items())}

    def get_all_commands(self) -> list[Command]:
        """Get all commands."""
        return list(self._commands.values())

    def search_commands(self, query: str) -> list[Command]:
        """Simple text search over commands (no ML)."""
        query_lower = query.lower()
        results = []
        for cmd in self._commands.values():
            if query_lower in cmd.searchable_text.lower():
                results.append(cmd)
        return results

    # ── Model Info ───────────────────────────────────────────

    def get_model_info(self) -> ModelInfo:
        """Get information about the loaded model."""
        techs = self.get_all_technologies()
        intents = set(cmd.intent for cmd in self._commands.values())

        return ModelInfo(
            embedding_model=self._embedder.model_name if self._embedder else "not loaded",
            embedding_dimension=self._embedder.dimension if self._embedder else 0,
            classifier_type=(
                self._classifier._config.model_type if self._classifier.is_fitted else "not loaded"
            ),
            num_commands=len(self._commands),
            num_technologies=len(techs),
            num_intents=len(intents),
            index_type=(
                "faiss" if self._vector_store and hasattr(self._vector_store, "_faiss") else "numpy"
            ),
            model_version="0.1.0",
            dataset_version="2026.08",
        )

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def command_count(self) -> int:
        return len(self._commands)

    # ── Add Custom Command ───────────────────────────────────

    def add_command(self, command: Command) -> None:
        """Add a single command and update the index (no retraining needed)."""
        self._commands[command.id] = command

        if self._embedder and self._vector_store:
            embedding = self._embedder.encode_single(command.searchable_text)
            import numpy as np
            self._vector_store.add(
                np.array([embedding]),
                [{"command_id": command.id}],
            )
            logger.info("Added command %s to index", command.id)


# ── Singleton ────────────────────────────────────────────────

_engine: InferenceEngine | None = None


def get_engine() -> InferenceEngine:
    """Get or create the global inference engine."""
    global _engine
    if _engine is None:
        _engine = InferenceEngine()
    return _engine


def reset_engine() -> None:
    """Reset the global engine (for testing)."""
    global _engine
    _engine = None
    reset_embedder()
