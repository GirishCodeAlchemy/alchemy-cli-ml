# AlchemyCLI AI

**Ask your terminal. Find the right command.**

AlchemyCLI AI is a local ML-powered developer command assistant that understands natural language questions and retrieves the most relevant, verified commands from a curated knowledge base.

```bash
alchemyai "how do I find pods using the most memory?"
```

```
Kubernetes › Resource Usage

  kubectl top pods --all-namespaces --sort-by=memory

  Shows pod CPU and memory usage, sorted by memory.

  Confidence: 96%
  Risk: SAFE
```

## Key Principles

- **Retrieval, not generation** — Commands come from a verified knowledge base, never invented
- **Local-first** — ML runs on your machine, no cloud APIs required
- **Safe by design** — Commands are classified by risk level, never executed

## Quick Start

```bash
# Install
pip install -e ".[dev,train]"

# Build the ML pipeline
make dataset      # Generate training data from knowledge base
make embeddings   # Build FAISS vector index
make train        # Train intent classifier
make evaluate     # Run evaluation metrics

# Use the CLI
alchemyai "restart kubernetes deployment"
alchemyai "find process using port 8080"
alchemyai "undo my last git commit"

# Start the API server
make serve

# Start the web UI
make web
```

## Architecture

```
                     User Question
                          │
                          ▼
                  Python ML/NLP Layer
                          │
                  Intent + Embedding
                          │
                          ▼
                   Semantic Search
                          │
                          ▼
              Verified Command Knowledge Base
                          │
                          ▼
                  Ranked Candidates
                          │
                          ▼
                  Safety Validation
                          │
                          ▼
                     CLI Response
```

## Project Structure

```
├── knowledge/           # Verified command YAML files
│   ├── kubernetes/
│   ├── docker/
│   ├── git/
│   ├── linux/
│   ├── python/
│   ├── go/
│   ├── rust/
│   ├── kafka/
│   └── terraform/
├── ml/                  # ML engine
│   ├── src/alchemy_ml/  # Core ML modules
│   ├── data/            # Training data
│   ├── models/          # Trained models
│   ├── tests/           # ML tests
│   └── config/          # Training configuration
├── cli/                 # Python CLI application
│   └── src/alchemyai/
├── api/                 # FastAPI REST service
├── web/                 # React web UI
├── tests/               # Integration tests
└── scripts/             # Utility scripts
```

## ML Engine

### Embedding Model
- **Base model**: `all-MiniLM-L6-v2` (384-dim, ~80MB)
- **Inference**: CPU-only, ~18ms/query
- **Vector search**: FAISS (with numpy fallback)

### Hybrid Ranking
```
final_score = 0.55 × semantic + 0.20 × keyword + 0.10 × technology + 0.10 × intent + 0.05 × tag
```

### Intent Classifier
- Logistic Regression on TF-IDF features
- Predicts technology and intent from query text

### Safety Classifier
- Pattern-based classification: safe / warning / dangerous
- Independent of ML model — never execute commands

## Technologies Covered

| Technology | Commands | Status |
|-----------|----------|--------|
| Kubernetes | ~80 | ✅ |
| Docker | ~60 | ✅ |
| Git | ~70 | ✅ |
| Linux | ~70 | ✅ |
| Python | ~40 | ✅ |
| Go | ~30 | ✅ |
| Rust | ~30 | ✅ |
| Kafka | ~35 | ✅ |
| Terraform | ~30 | ✅ |

## CLI Usage

```bash
# Natural language search
alchemyai "how do I restart a kubernetes deployment?"

# Interactive mode
alchemyai

# Technology browsing
alchemyai kubernetes
alchemyai docker

# JSON output (for scripts)
alchemyai "find port 8080" --json

# Command-only output
alchemyai "find port 8080" --cmd

# Show match explanation
alchemyai "restart deployment" --explain

# Copy result to clipboard
alchemyai "find port 8080" --copy

# Search modes
alchemyai --mode semantic "restart deployment"
alchemyai --mode keyword "kubectl rollout"
alchemyai --mode hybrid "restart deployment"

# Model info
alchemyai model info
```

## API

```bash
# Start server
make serve

# Endpoints
GET  /api/v1/health
GET  /api/v1/model
POST /api/v1/ask          {"query": "restart k8s deployment"}
GET  /api/v1/search?q=pods
GET  /api/v1/commands
GET  /api/v1/commands/:id
GET  /api/v1/categories
GET  /api/v1/technologies
```

## Docker

```bash
docker compose up          # Start API + web
docker compose -f docker-compose.dev.yml up   # Development
docker compose -f docker-compose.prod.yml up  # Production
```

## Development

```bash
make setup        # Install dependencies
make test         # Run all tests
make lint         # Run linter
make format       # Auto-format code
make validate     # Lint + typecheck + test
```

## Custom Commands

Add your own commands to `~/.config/alchemyai/commands/`:

```yaml
- id: restart-company-service
  technology: company
  category: services
  name: Restart company service
  command: companyctl service restart <service>
  description: Restart an internal company service.
  intent: restart_service
  tags: [restart, service]
  risk: warning
```

Custom commands are indexed immediately — no retraining needed.

## Privacy

- No telemetry by default
- All ML inference runs locally
- Query history stored locally only
- No network calls during search

## License

MIT
