# ── Build Args ────────────────────────────────────────────────
# DEVICE=cpu  → CPU-only torch (~200MB), fits 512MB RAM (Render free)
# DEVICE=cuda → Full torch with CUDA (~2GB), needs GPU host
ARG DEVICE=cpu

# ── Base ──────────────────────────────────────────────────────
FROM python:3.12-slim AS base

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Copy source code and config (needed for pip install -e)
COPY README.md pyproject.toml ./
COPY ml/ ml/
COPY cli/ cli/
COPY api/ api/
COPY knowledge/ knowledge/

# ── CPU stage ─────────────────────────────────────────────────
FROM base AS deps-cpu
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -e ".[train]"

# ── GPU stage ─────────────────────────────────────────────────
FROM base AS deps-cuda
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu121 && \
    pip install --no-cache-dir -e ".[train]"

# ── Final ─────────────────────────────────────────────────────
FROM deps-${DEVICE} AS final

# Set device for the ML engine
ENV ALCHEMYAI_EMBEDDING__DEVICE=${DEVICE}

# Build dataset and index at image build time
RUN python -m alchemy_ml.cli dataset && \
    python -m alchemy_ml.cli embeddings && \
    python -m alchemy_ml.cli train

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
