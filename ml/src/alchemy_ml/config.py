"""Configuration for AlchemyCLI AI ML engine."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


def _project_root() -> Path:
    """Return the project root (parent of ml/)."""
    return Path(__file__).resolve().parents[3]


def _ml_root() -> Path:
    """Return the ml/ directory."""
    return Path(__file__).resolve().parents[2]


class EmbeddingConfig(BaseModel):
    """Embedding model configuration."""

    model_name: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    max_seq_length: int = 256
    batch_size: int = 64
    normalize: bool = True
    device: str = "cpu"


class ClassifierConfig(BaseModel):
    """Intent classifier configuration."""

    model_type: str = "logistic_regression"  # logistic_regression | linear_svc
    C: float = 1.0
    max_iter: int = 1000
    tfidf_max_features: int = 10000
    tfidf_ngram_range: tuple[int, int] = (1, 3)
    min_samples_per_class: int = 3


class RetrievalConfig(BaseModel):
    """Retrieval configuration."""

    top_k: int = 10
    faiss_index_type: str = "flat"  # flat | ivf
    faiss_nprobe: int = 10
    min_similarity: float = 0.3


class RankingConfig(BaseModel):
    """Hybrid ranking weights — must sum to 1.0."""

    semantic_weight: float = 0.55
    keyword_weight: float = 0.20
    technology_weight: float = 0.10
    intent_weight: float = 0.10
    tag_weight: float = 0.05


class SafetyConfig(BaseModel):
    """Safety classifier configuration."""

    dangerous_patterns: list[str] = Field(default_factory=lambda: [
        r"rm\s+-rf\s+/",
        r"mkfs\.",
        r"dd\s+if=",
        r":\(\)\s*\{",
        r">\s*/dev/sd",
        r"chmod\s+-R\s+777\s+/",
    ])
    require_confirmation_for: list[str] = Field(default_factory=lambda: [
        "dangerous",
        "warning",
    ])


class TrainingConfig(BaseModel):
    """Training pipeline configuration."""

    seed: int = 42
    epochs: int = 3
    batch_size: int = 32
    learning_rate: float = 2e-5
    warmup_ratio: float = 0.1
    train_split: float = 0.70
    val_split: float = 0.15
    test_split: float = 0.15
    negative_ratio: int = 5  # hard negatives per positive


class CacheConfig(BaseModel):
    """LRU cache configuration."""

    max_size: int = 1024
    ttl_seconds: int = 3600


class ContextConfig(BaseModel):
    """Conversation context configuration."""

    max_history: int = 10
    retention_minutes: int = 30


class Config(BaseSettings):
    """Main configuration for AlchemyCLI AI."""

    # Paths
    project_root: Path = Field(default_factory=_project_root)
    ml_root: Path = Field(default_factory=_ml_root)

    # Sub-configs
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    classifier: ClassifierConfig = Field(default_factory=ClassifierConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    ranking: RankingConfig = Field(default_factory=RankingConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)

    # Thresholds
    confidence_threshold: float = 0.50
    high_confidence: float = 0.90
    medium_confidence: float = 0.75

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    model_config = {"env_prefix": "ALCHEMYAI_", "env_nested_delimiter": "__"}

    @property
    def knowledge_dir(self) -> Path:
        return self.project_root / "knowledge"

    @property
    def models_dir(self) -> Path:
        return self.ml_root / "models"

    @property
    def data_dir(self) -> Path:
        return self.ml_root / "data"

    @property
    def faiss_index_path(self) -> Path:
        return self.data_dir / "processed" / "command_embeddings.faiss"

    @property
    def metadata_path(self) -> Path:
        return self.data_dir / "processed" / "command_metadata.json"

    @property
    def embedding_cache_path(self) -> Path:
        return self.data_dir / "processed" / "embeddings.npy"

    @property
    def classifier_path(self) -> Path:
        return self.models_dir / "classifier"

    @property
    def user_commands_dir(self) -> Path:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return config_home / "alchemyai" / "commands"

    @property
    def user_config_path(self) -> Path:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return config_home / "alchemyai" / "config.yaml"

    @property
    def context_path(self) -> Path:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return config_home / "alchemyai" / "context.json"

    @property
    def history_path(self) -> Path:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return config_home / "alchemyai" / "history.jsonl"

    @property
    def favorites_path(self) -> Path:
        config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        return config_home / "alchemyai" / "favorites.json"

    @classmethod
    def load(cls, config_path: Path | None = None) -> Config:
        """Load configuration, merging defaults with optional YAML overrides."""
        config = cls()
        if config_path and config_path.exists():
            with open(config_path) as f:
                overrides = yaml.safe_load(f) or {}
            config = cls(**overrides)
        # Also check user config
        if config.user_config_path.exists():
            with open(config.user_config_path) as f:
                user_overrides = yaml.safe_load(f) or {}
            # Merge user overrides (user config takes precedence)
            merged = config.model_dump()
            _deep_merge(merged, user_overrides)
            config = cls(**merged)
        return config


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> None:
    """Deep merge override into base dict in place."""
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


# Singleton config instance
_config: Config | None = None


def get_config() -> Config:
    """Get or create the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.load()
    return _config


def reset_config() -> None:
    """Reset the global configuration (for testing)."""
    global _config
    _config = None
