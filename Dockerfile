FROM python:3.12-slim AS base

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy source code and config first (needed for pip install -e)
COPY README.md pyproject.toml ./
COPY ml/ ml/
COPY cli/ cli/
COPY api/ api/
COPY knowledge/ knowledge/

# Python dependencies
RUN pip install --no-cache-dir -e ".[train]"

# Build dataset and index on image build
RUN python -m alchemy_ml.cli dataset && \
    python -m alchemy_ml.cli embeddings && \
    python -m alchemy_ml.cli train

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
