"""FastAPI application for AlchemyCLI AI.

Provides REST API endpoints for command search, listing,
and model information.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from alchemy_ml.config import get_config
from alchemy_ml.inference import InferenceEngine
from alchemy_ml.models import RiskLevel

logger = logging.getLogger(__name__)

# Global engine instance
engine: InferenceEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the ML engine on startup."""
    global engine
    logger.info("Initializing AlchemyCLI AI engine...")
    engine = InferenceEngine()
    engine.initialize()
    logger.info("Engine ready. %d commands loaded.", engine.command_count)
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="AlchemyCLI AI",
    description="Ask your terminal. Find the right command.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
config = get_config()
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response Models ──────────────────────────────────


class AskRequest(BaseModel):
    query: str
    top_k: int = 5
    mode: str = "hybrid"
    explain: bool = False


class SearchResultResponse(BaseModel):
    command_id: str
    command: str
    name: str
    description: str
    technology: str
    category: str
    intent: str
    confidence: float
    risk: str
    tags: list[str] = Field(default_factory=list)
    documentation_url: str = ""
    related_commands: list[str] = Field(default_factory=list)
    explanation: dict[str, Any] | None = None


class ClarificationResponse(BaseModel):
    message: str
    options: list[dict[str, str]] = Field(default_factory=list)


class AskResponseModel(BaseModel):
    query: str
    results: list[SearchResultResponse] = Field(default_factory=list)
    clarification: ClarificationResponse | None = None


class CommandResponse(BaseModel):
    id: str
    technology: str
    category: str
    name: str
    intent: str
    command: str
    description: str
    tags: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    risk: str
    documentation_url: str = ""
    verified_at: str = ""


class ModelInfoResponse(BaseModel):
    embedding_model: str
    embedding_dimension: int
    classifier_type: str
    num_commands: int
    num_technologies: int
    num_intents: int
    index_type: str
    model_version: str
    dataset_version: str


class HealthResponse(BaseModel):
    status: str
    version: str
    commands: int
    uptime_seconds: float


_start_time = time.monotonic()


# ── Endpoints ────────────────────────────────────────────────


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if engine and engine.is_loaded else "degraded",
        version="0.1.0",
        commands=engine.command_count if engine else 0,
        uptime_seconds=round(time.monotonic() - _start_time, 1),
    )


@app.get("/api/v1/model", response_model=ModelInfoResponse)
async def model_info():
    """Get model information."""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    info = engine.get_model_info()
    return ModelInfoResponse(**info.model_dump())


@app.post("/api/v1/ask", response_model=AskResponseModel)
async def ask(request: AskRequest):
    """Process a natural language query and return matching commands."""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    response = engine.ask(
        query=request.query,
        top_k=request.top_k,
        mode=request.mode,
        explain=request.explain,
    )

    results = []
    for r in response.results:
        results.append(SearchResultResponse(
            command_id=r.command_id,
            command=r.command,
            name=r.name,
            description=r.description,
            technology=r.technology,
            category=r.category,
            intent=r.intent,
            confidence=r.confidence,
            risk=r.risk.value,
            tags=r.tags,
            documentation_url=r.documentation_url,
            related_commands=r.related_commands,
            explanation=r.explanation.model_dump() if r.explanation else None,
        ))

    clarification = None
    if response.clarification:
        clarification = ClarificationResponse(
            message=response.clarification.message,
            options=[opt.model_dump() for opt in response.clarification.options],
        )

    return AskResponseModel(
        query=response.query,
        results=results,
        clarification=clarification,
    )


@app.get("/api/v1/search")
async def search(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(10, description="Number of results"),
    mode: str = Query("hybrid", description="Search mode"),
):
    """Search commands (GET version of /ask)."""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    response = engine.ask(query=q, top_k=top_k, mode=mode)

    return {
        "query": q,
        "results": [
            {
                "command_id": r.command_id,
                "command": r.command,
                "name": r.name,
                "confidence": r.confidence,
                "technology": r.technology,
                "risk": r.risk.value,
            }
            for r in response.results
        ],
    }


@app.get("/api/v1/commands", response_model=list[CommandResponse])
async def list_commands(
    technology: str | None = Query(None, description="Filter by technology"),
    limit: int = Query(100, description="Max results"),
    offset: int = Query(0, description="Offset"),
):
    """List all commands, optionally filtered by technology."""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    if technology:
        commands = engine.get_commands_by_technology(technology)
    else:
        commands = engine.get_all_commands()

    commands = commands[offset:offset + limit]

    return [
        CommandResponse(
            id=cmd.id,
            technology=cmd.technology,
            category=cmd.category,
            name=cmd.name,
            intent=cmd.intent,
            command=cmd.command,
            description=cmd.description,
            tags=cmd.tags,
            aliases=cmd.aliases,
            risk=cmd.risk.value,
            documentation_url=cmd.doc_url,
            verified_at=cmd.verified_at,
        )
        for cmd in commands
    ]


@app.get("/api/v1/commands/{command_id}", response_model=CommandResponse)
async def get_command(command_id: str):
    """Get a specific command by ID."""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    cmd = engine.get_command(command_id)
    if not cmd:
        raise HTTPException(status_code=404, detail=f"Command not found: {command_id}")

    return CommandResponse(
        id=cmd.id,
        technology=cmd.technology,
        category=cmd.category,
        name=cmd.name,
        intent=cmd.intent,
        command=cmd.command,
        description=cmd.description,
        tags=cmd.tags,
        aliases=cmd.aliases,
        risk=cmd.risk.value,
        documentation_url=cmd.doc_url,
        verified_at=cmd.verified_at,
    )


@app.get("/api/v1/categories")
async def list_categories():
    """List all categories grouped by technology."""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    return engine.get_all_categories()


@app.get("/api/v1/technologies")
async def list_technologies():
    """List all available technologies with command counts."""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    techs = {}
    for t in engine.get_all_technologies():
        techs[t] = len(engine.get_commands_by_technology(t))
    return techs


@app.get("/api/v1/recent")
async def recent():
    """Get recent queries (from in-memory context)."""
    if not engine:
        return {"queries": []}

    return {"queries": engine._context[-10:]}


@app.post("/api/v1/reload")
async def reload_engine():
    """Reload the engine (re-index commands)."""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")

    engine.load_commands()
    engine.build_index()
    engine.save_index()
    return {"status": "reloaded", "commands": engine.command_count}
