# AlchemyCLI AI — Getting Started Guide

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for web UI)
- **Git**

---

## 1. Clone & Setup

```bash
git clone https://github.com/GirishCodeAlchemy/alchemy-cli-ml.git
cd alchemy-cli-ml
```

### Create Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

### Install dependencies

```bash
pip install -e ".[dev,train]"
```

> **Corporate proxy / SSL issues?** Use your internal PyPI mirror:
> ```bash
> pip install --index-url https://your-internal-pypi/simple/ \
>     --trusted-host your-internal-pypi \
>     -e ".[dev,train]"
> ```

> **HuggingFace model download blocked?** The system will auto-fallback to a TF-IDF embedder.
> To force the fallback explicitly, set: `export ALCHEMYAI_FORCE_FALLBACK=1`

---

## 2. Run the ML Pipeline

The ML pipeline has 4 steps. Run them in order:

### Step 1: Build the training dataset

```bash
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli dataset
```

This reads all `knowledge/*.yaml` files and generates:
- `ml/data/processed/train.jsonl`
- `ml/data/processed/validation.jsonl`
- `ml/data/processed/test.jsonl`

Expected output:
```
Dataset built: ~13800 examples from 558 commands
```

### Step 2: Build the vector index (embeddings)

```bash
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli embeddings
```

This generates embeddings for all commands and builds a FAISS index.

> **First run** downloads the `all-MiniLM-L6-v2` model (~80MB) from HuggingFace.
> If download fails (corporate proxy), the system falls back to TF-IDF+SVD embeddings automatically.

Expected output:
```
Loaded 558 commands
Building index...
Index built in X.Xs
Index saved.
```

### Step 3: Train the intent classifier

```bash
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli train
```

Expected output:
```
Training on ~9660 examples...
Training complete:
  Tech accuracy:    ~95%
  Intent accuracy:  ~85%
  Technologies:     9
  Intents:          ~150
```

### Step 4: Evaluate (optional)

```bash
PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli evaluate
```

### Or run all steps at once:

```bash
make ml-pipeline
```

---

## 3. Use the CLI

### Ask a question (main usage)

```bash
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli "how do I restart a kubernetes deployment?"
```

### More examples

```bash
# Find commands by natural language
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli "find process using port 8080"
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli "undo my last git commit but keep changes"
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli "show kafka consumer lag"
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli "create a python virtual environment"

# Browse by technology
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli kubernetes
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli docker
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli git

# List all technologies
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli list

# JSON output (for scripting)
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli --json "restart k8s deployment"

# Output only the command string
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli --cmd "find port 8080"

# Show why a command matched
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli --explain "restart deployment"

# Copy result to clipboard
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli --copy "find port 8080"

# Choose search mode
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli --mode semantic "restart deployment"
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli --mode keyword "kubectl rollout"

# Model info
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli model info
```

### Interactive mode

```bash
PYTHONPATH=ml/src:cli/src python -m alchemyai.cli
```

Then type questions at the `You:` prompt:
```
You: how do I find pods using the most memory?
You: restart it
You: /help
You: /exit
```

### Tip: Create a shell alias

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias alchemyai='PYTHONPATH=/path/to/alchemy-cli-ml/ml/src:/path/to/alchemy-cli-ml/cli/src python -m alchemyai.cli'
```

Then just:
```bash
alchemyai "restart k8s deployment"
```

---

## 4. Start the API Server

```bash
PYTHONPATH=ml/src:cli/src python -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

Or using Make:
```bash
make serve
```

### Test the API

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Ask a question
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "restart kubernetes deployment"}'

# List technologies
curl http://localhost:8000/api/v1/technologies

# List commands for a technology
curl http://localhost:8000/api/v1/commands?technology=kubernetes&limit=10

# Search
curl "http://localhost:8000/api/v1/search?q=find+port+8080"
```

### API Docs (Swagger)

Open in browser: http://localhost:8000/api/docs

---

## 5. Start the Web UI

```bash
cd web
npm install
npm run dev
```

Or using Make:
```bash
make web
```

Open in browser: http://localhost:3000

> **Note:** The web UI requires the API server running on port 8000.
> Start the API first (step 4), then the web UI.

---

## 6. Run with Docker

### Development (with hot reload)

```bash
docker compose -f docker-compose.dev.yml up
```

### Production

```bash
docker compose -f docker-compose.prod.yml up -d
```

### Build only

```bash
docker compose build
```

Services:
- **API**: http://localhost:8000
- **Web**: http://localhost:3000
- **API Docs**: http://localhost:8000/api/docs

---

## 7. Run Tests

```bash
# All tests
PYTHONPATH=ml/src:cli/src python -m pytest ml/tests/ cli/tests/ api/tests/ -v

# Only ML tests
PYTHONPATH=ml/src:cli/src python -m pytest ml/tests/ -v

# Only CLI tests
PYTHONPATH=ml/src:cli/src python -m pytest cli/tests/ -v

# Only API tests
PYTHONPATH=ml/src:cli/src python -m pytest api/tests/ -v

# With coverage
PYTHONPATH=ml/src:cli/src python -m pytest --cov=alchemy_ml --cov=alchemyai --cov-report=term
```

### Validate knowledge base YAML

```bash
python scripts/validate_dataset.py
```

---

## 8. Add Custom Commands

Create a YAML file at `~/.config/alchemyai/commands/my-commands.yaml`:

```yaml
- id: my-company-deploy
  technology: company
  category: deployment
  name: Deploy to staging
  intent: deploy_staging
  command: deploy-tool push --env staging
  description: Deploy the current branch to the staging environment.
  tags: [deploy, staging, company]
  aliases:
    - deploy to staging
    - push to staging
  examples:
    - query: "deploy to staging"
    - query: "push my changes to staging"
  risk: warning
  documentation:
    url: https://internal-docs.example.com/deploy
  verified_at: "2026-08-01"
```

Custom commands are picked up automatically — no retraining needed.

---

## Quick Reference

| Task | Command |
|------|---------|
| Install | `pip install -e ".[dev,train]"` |
| Build dataset | `PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli dataset` |
| Build index | `PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli embeddings` |
| Train classifier | `PYTHONPATH=ml/src:cli/src python -m alchemy_ml.cli train` |
| Ask a question | `PYTHONPATH=ml/src:cli/src python -m alchemyai.cli "your question"` |
| Interactive mode | `PYTHONPATH=ml/src:cli/src python -m alchemyai.cli` |
| Start API | `PYTHONPATH=ml/src:cli/src python -m uvicorn api.app:app --reload --port 8000` |
| Start Web | `cd web && npm install && npm run dev` |
| Run tests | `PYTHONPATH=ml/src:cli/src python -m pytest ml/tests/ -v` |
| Docker | `docker compose up` |

---

## Troubleshooting

### SSL / Corporate Proxy errors downloading model

Set these environment variables before running:

```bash
export REQUESTS_CA_BUNDLE=""
export CURL_CA_BUNDLE=""
export HF_HUB_DISABLE_TELEMETRY=1
```

Or disable SSL verification in Python:

```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

If HuggingFace is completely blocked, the system automatically falls back to TF-IDF+SVD embeddings (lower quality but fully offline).

### "Module not found" errors

Always set PYTHONPATH:

```bash
export PYTHONPATH=ml/src:cli/src
```

Or add it to your `.env` file.

### Model not loaded / low quality results

Make sure you ran all 3 pipeline steps:
1. `python -m alchemy_ml.cli dataset`
2. `python -m alchemy_ml.cli embeddings`
3. `python -m alchemy_ml.cli train`

### Web UI shows "No results" / API connection error

Make sure the API server is running on port 8000 before starting the web UI.
