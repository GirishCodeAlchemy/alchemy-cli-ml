"""Data models for AlchemyCLI AI."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Command risk classification."""

    SAFE = "safe"
    WARNING = "warning"
    DANGEROUS = "dangerous"


class CommandDoc(BaseModel):
    """Official documentation reference."""

    url: str


class Command(BaseModel):
    """A verified command in the knowledge base."""

    id: str
    technology: str
    category: str
    name: str
    intent: str
    command: str
    description: str
    tags: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    examples: list[dict[str, str]] = Field(default_factory=list)
    risk: RiskLevel = RiskLevel.SAFE
    documentation: CommandDoc | None = None
    verified_at: str = ""

    @property
    def searchable_text(self) -> str:
        """Combine all searchable fields into one text block for embedding."""
        parts = [
            self.name,
            self.description,
            self.command,
            self.technology,
            self.category,
            self.intent.replace("_", " "),
            " ".join(self.tags),
            " ".join(self.aliases),
        ]
        for ex in self.examples:
            if "query" in ex:
                parts.append(ex["query"])
        return " ".join(parts)

    @property
    def doc_url(self) -> str:
        """Get documentation URL."""
        return self.documentation.url if self.documentation else ""


class SearchResult(BaseModel):
    """A single search result returned to the user."""

    command_id: str
    command: str
    name: str
    description: str
    technology: str
    category: str
    intent: str
    confidence: float
    risk: RiskLevel
    tags: list[str] = Field(default_factory=list)
    documentation_url: str = ""
    related_commands: list[str] = Field(default_factory=list)
    explanation: SearchExplanation | None = None


class SearchExplanation(BaseModel):
    """Explains why a command matched a query."""

    technology_detected: str = ""
    intent_detected: str = ""
    matched_tags: list[str] = Field(default_factory=list)
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    technology_score: float = 0.0
    intent_score: float = 0.0
    tag_score: float = 0.0
    final_score: float = 0.0


class AskResponse(BaseModel):
    """Response to an ask/search query."""

    query: str
    results: list[SearchResult] = Field(default_factory=list)
    clarification: ClarificationRequest | None = None
    debug: dict[str, Any] | None = None


class ClarificationRequest(BaseModel):
    """Request for user clarification when query is ambiguous."""

    message: str
    options: list[ClarificationOption] = Field(default_factory=list)


class ClarificationOption(BaseModel):
    """A clarification option."""

    label: str
    technology: str = ""
    intent: str = ""
    query: str = ""


class ModelInfo(BaseModel):
    """Information about the loaded ML model."""

    embedding_model: str = ""
    embedding_dimension: int = 0
    classifier_type: str = ""
    num_commands: int = 0
    num_technologies: int = 0
    num_intents: int = 0
    index_type: str = ""
    model_version: str = ""
    dataset_version: str = ""


class TrainingExample(BaseModel):
    """A training example linking a query to a command."""

    query: str
    command_id: str
    technology: str = ""
    intent: str = ""


class EvaluationMetrics(BaseModel):
    """Evaluation metrics for the ML model."""

    recall_at_1: float = 0.0
    recall_at_3: float = 0.0
    recall_at_5: float = 0.0
    mrr: float = 0.0
    precision_at_1: float = 0.0
    precision_at_3: float = 0.0
    intent_accuracy: float = 0.0
    safety_accuracy: float = 0.0
    num_queries: int = 0
    num_commands: int = 0
    dataset_version: str = ""
