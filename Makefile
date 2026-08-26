.PHONY: setup install dev test lint validate dataset embeddings train evaluate benchmark build docker release clean web web-build web-dev serve help

PYTHON := python3
UV := uv
PIP := pip

# ─── Setup ────────────────────────────────────────────────────

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Full project setup
	$(UV) sync || $(PIP) install -e ".[dev,train]"
	@echo "\n✓ Setup complete. Run 'make dataset' to build the training data."

install: ## Install in production mode
	$(PIP) install -e .

dev: ## Install with dev dependencies
	$(PIP) install -e ".[dev,train]"

# ─── ML Pipeline ──────────────────────────────────────────────

dataset: ## Build training dataset from knowledge base
	$(PYTHON) -m alchemy_ml.cli dataset
	@echo "✓ Dataset built"

embeddings: ## Generate embeddings and build FAISS index
	$(PYTHON) -m alchemy_ml.cli embeddings
	@echo "✓ Embeddings built"

train: ## Train intent classifier
	$(PYTHON) -m alchemy_ml.cli train
	@echo "✓ Training complete"

evaluate: ## Evaluate model on test data
	$(PYTHON) -m alchemy_ml.cli evaluate
	@echo "✓ Evaluation complete"

benchmark: ## Run benchmark with latency measurements
	$(PYTHON) -m alchemy_ml.cli benchmark

ml-pipeline: dataset embeddings train evaluate ## Run full ML pipeline
	@echo "✓ Full ML pipeline complete"

# ─── Testing ──────────────────────────────────────────────────

test: ## Run all tests
	$(PYTHON) -m pytest ml/tests/ cli/tests/ api/tests/ tests/ -v

test-ml: ## Run ML tests only
	$(PYTHON) -m pytest ml/tests/ -v

test-cli: ## Run CLI tests only
	$(PYTHON) -m pytest cli/tests/ -v

test-api: ## Run API tests only
	$(PYTHON) -m pytest api/tests/ -v

test-cov: ## Run tests with coverage
	$(PYTHON) -m pytest --cov=alchemy_ml --cov=alchemyai --cov-report=html --cov-report=term

regression: ## Run ML regression tests
	$(PYTHON) -m alchemy_ml.cli regression

# ─── Code Quality ─────────────────────────────────────────────

lint: ## Run linter
	ruff check ml/src/ cli/src/ api/ tests/
	ruff format --check ml/src/ cli/src/ api/ tests/

format: ## Auto-format code
	ruff check --fix ml/src/ cli/src/ api/ tests/
	ruff format ml/src/ cli/src/ api/ tests/

typecheck: ## Run type checker
	mypy ml/src/ cli/src/ api/

validate: lint typecheck test ## Run all validation checks

# ─── Web UI ───────────────────────────────────────────────────

web-install: ## Install web dependencies
	cd web && npm install

web-dev: ## Start web dev server
	cd web && npm run dev

web-build: ## Build web for production
	cd web && npm run build

web: web-install web-dev ## Install and start web dev server

# ─── Server ───────────────────────────────────────────────────

serve: ## Start API server
	$(PYTHON) -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

serve-prod: ## Start API server in production mode
	$(PYTHON) -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --workers 4

# ─── Docker ───────────────────────────────────────────────────

docker: ## Build Docker images
	docker compose build

docker-up: ## Start all services
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

docker-dev: ## Start development environment
	docker compose -f docker-compose.dev.yml up

docker-prod: ## Start production environment
	docker compose -f docker-compose.prod.yml up -d

# ─── Build & Release ─────────────────────────────────────────

build: ## Build Python package
	$(PYTHON) -m build

release: validate build ## Full release process
	@echo "✓ Release build complete"
	@echo "  Upload with: twine upload dist/*"

# ─── Cleanup ──────────────────────────────────────────────────

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info
	rm -rf ml/reports/*.png ml/reports/*.html
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Cleaned"

clean-models: ## Clean generated models and indices
	rm -rf ml/models/embedding/*/
	rm -rf ml/models/classifier/*/
	rm -rf ml/data/processed/*.faiss
	rm -rf ml/data/processed/*.npy
	rm -rf ml/data/processed/*.json
	rm -rf ml/data/processed/*.jsonl
	@echo "✓ Models cleaned"
