# AlchemyCLI Web UI — Local Development & Vercel Deployment Guide

## Table of Contents

- [Prerequisites](#prerequisites)
- [Project Overview](#project-overview)
- [Local Development Setup](#local-development-setup)
- [Running Locally](#running-locally)
- [Environment Variables](#environment-variables)
- [Deploying to Vercel](#deploying-to-vercel)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Tool       | Version  | Check Command      |
| ---------- | -------- | ------------------ |
| Node.js    | ≥ 18.x   | `node --version`   |
| npm        | ≥ 9.x    | `npm --version`    |
| Python     | ≥ 3.11   | `python --version` |
| Git        | any      | `git --version`    |
| Make       | any      | `make --version`   |

---

## Project Overview

```
alchemy-cli-ml/
├── api/                 # FastAPI REST backend (port 8000)
├── web/                 # React + Vite + TypeScript + Tailwind CSS (port 3000)
│   ├── src/
│   │   ├── api/         # API client (client.ts, types.ts)
│   │   ├── components/  # Reusable UI components
│   │   ├── hooks/       # Custom React hooks
│   │   └── pages/       # Route pages (Home, Command, Category, 404)
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── package.json
├── ml/                  # ML engine (embeddings, classifiers)
├── knowledge/           # YAML command knowledge base
├── Makefile             # Project-wide build targets
└── docker-compose.yml   # Full-stack Docker setup
```

**Tech Stack:**

- **Frontend:** React 18, TypeScript, Vite 5, Tailwind CSS 3, React Router 6
- **Backend:** FastAPI, Uvicorn, sentence-transformers, FAISS
- **Styling:** Tailwind CSS with custom brand/navy color palettes, dark mode support

---

## Local Development Setup

### Option 1: Using Makefile (Recommended)

From the project root (`alchemy-cli-ml/`):

```bash
# 1. Full project setup (Python venv + dependencies + web install)
make setup

# 2. Run the ML pipeline (first time only — builds models & indices)
make ml-pipeline

# 3. Start the API server (Terminal 1)
make serve

# 4. Start the web dev server (Terminal 2)
make web
```

### Option 2: Manual Setup

#### Step 1 — Set up the Backend API

```bash
# From project root
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# Install Python dependencies
pip install -e ".[dev]"

# Build the ML pipeline (first time only)
make ml-pipeline
# Or manually:
#   python -m alchemy_ml.cli dataset build
#   python -m alchemy_ml.cli embeddings build
#   python -m alchemy_ml.cli train

# Start the API server
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`. Verify:

```bash
curl http://localhost:8000/api/v1/health
```

API docs are at `http://localhost:8000/api/docs` (Swagger UI).

#### Step 2 — Set up the Web Frontend

```bash
# From project root
cd web

# Install dependencies
npm install

# Start dev server
npm run dev
```

The web UI will be available at `http://localhost:3000`.

Vite automatically proxies `/api` requests to `http://localhost:8000` during development (configured in `vite.config.ts`).

### Option 3: Docker Compose (Full Stack)

```bash
# From project root — starts both API and Web
docker-compose up --build

# Or for development with hot-reload:
docker-compose -f docker-compose.dev.yml up --build
```

- API: `http://localhost:8000`
- Web: `http://localhost:3000`

---

## Running Locally

### Available npm Scripts

| Command           | Description                          |
| ----------------- | ------------------------------------ |
| `npm run dev`     | Start Vite dev server (port 3000)    |
| `npm run build`   | TypeScript check + production build  |
| `npm run preview` | Preview the production build locally |
| `npm run lint`    | Run ESLint                           |

### Available Makefile Targets (from project root)

| Target        | Description                    |
| ------------- | ------------------------------ |
| `make web`    | Install deps + start dev server|
| `make web-install` | Install web dependencies  |
| `make web-dev`| Start web dev server           |
| `make web-build`| Build web for production     |
| `make serve`  | Start API server               |

### Verifying Everything Works

1. Start the API: `make serve` (Terminal 1)
2. Start the web: `make web` (Terminal 2)
3. Open `http://localhost:3000`
4. Try searching for a command like "how to restart a kubernetes deployment"

---

## Environment Variables

### Frontend (Vite)

Create a `.env` file in the `web/` directory:

```env
# API base URL (only needed in production or when API is on a different host)
VITE_API_URL=http://localhost:8000
```

> **Note:** In development, the Vite proxy handles API routing automatically. `VITE_API_URL` is only needed when the API runs on a separate host (e.g., production).

### Backend

| Variable              | Default           | Description          |
| --------------------- | ----------------- | -------------------- |
| `ALCHEMYAI_API_HOST`  | `0.0.0.0`        | API bind host        |
| `ALCHEMYAI_API_PORT`  | `8000`            | API bind port        |

---

## Deploying to Vercel

### Step 1 — Push Code to GitHub

Ensure your code is pushed to GitHub:

```bash
git add .
git commit -m "chore: prepare web UI for Vercel deployment"
git push origin main
```

### Step 2 — Create a Vercel Account

1. Go to [vercel.com](https://vercel.com) and sign up with your GitHub account
2. Authorize Vercel to access your repositories

### Step 3 — Import the Project

1. Click **"Add New"** → **"Project"** in the Vercel dashboard
2. Select the **`GirishCodeAlchemy/alchemy-cli-ml`** repository
3. Click **"Import"**

### Step 4 — Configure Build Settings

| Setting              | Value            |
| -------------------- | ---------------- |
| **Framework Preset** | Vite             |
| **Root Directory**   | `web`            |
| **Build Command**    | `npm run build`  |
| **Output Directory** | `dist`           |
| **Install Command**  | `npm install`    |

### Step 5 — Set Environment Variables

In **Settings → Environment Variables**, add:

| Name            | Value                          | Environment |
| --------------- | ------------------------------ | ----------- |
| `VITE_API_URL`  | `https://your-api-domain.com`  | Production  |

> **Important:** Replace `https://your-api-domain.com` with your actual deployed API URL. Without this, the frontend will try to reach `http://localhost:8000` which won't work in production.

### Step 6 — Deploy

Click **"Deploy"**. Vercel will:

1. Clone your repo
2. Navigate to the `web/` root directory
3. Run `npm install`
4. Run `npm run build` (TypeScript check + Vite build)
5. Deploy the `dist/` output to the Vercel CDN

### Step 7 — Configure SPA Routing

Since this is a React SPA with client-side routing, create a `vercel.json` in the `web/` directory to handle route rewrites:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

This ensures routes like `/commands/kubernetes/restart` don't return 404 on page refresh.

### Automatic Deployments

Once connected, Vercel automatically deploys:

- **Production** — on every push to `main`
- **Preview** — on every pull request (unique URL per PR)

### Vercel CLI (Alternative)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from the web directory
cd web
vercel

# Follow the prompts:
#   - Link to existing project or create new
#   - Set root directory to ./
#   - Framework: Vite
#   - Build command: npm run build
#   - Output: dist

# Production deploy
vercel --prod
```

---

## Troubleshooting

### API Connection Issues in Dev

**Symptom:** Network errors when searching for commands.

**Fix:** Ensure the API server is running on port 8000:

```bash
make serve
# or
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### Build Fails with TypeScript Errors

**Fix:** Run the type checker separately to see errors:

```bash
cd web
npx tsc --noEmit
```

### Blank Page After Vercel Deploy

**Cause:** Missing SPA rewrite rules.

**Fix:** Add the `vercel.json` with rewrites as described in Step 7 above.

### API Not Reachable in Production

**Cause:** `VITE_API_URL` not set or pointing to localhost.

**Fix:**

1. Deploy your API backend separately (e.g., Railway, Render, Fly.io, or Docker on a VPS)
2. Set `VITE_API_URL` in Vercel environment variables to the deployed API URL
3. Ensure your API has CORS configured to allow requests from your Vercel domain

### CORS Errors in Production

The FastAPI backend has CORS middleware. Ensure your Vercel domain is allowed:

```python
# api/main.py — update allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-app.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Port Conflicts

If port 3000 or 8000 is already in use:

```bash
# Find and kill the process
lsof -i :3000
kill -9 <PID>
```

Or change ports:

- Web: Edit `vite.config.ts` → `server.port`
- API: `uvicorn api.app:app --port 8001`
