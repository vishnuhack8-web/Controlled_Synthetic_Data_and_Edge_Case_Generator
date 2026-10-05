# SynthEdge — AI Synthetic Data & Edge-Case Generation Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Node](https://img.shields.io/badge/node-18%2B-green)

SynthEdge generates realistic, privacy-preserving synthetic datasets **and the rare edge cases real data almost never contains** — for ML training, software testing and analytics.

Describe a machine or system in plain English. A **local, offline LLM (Ollama)** extracts the parameters, the generator produces data for any schema, edge-case failures are injected, and the platform proves the value by training a model **with vs. without** those edge cases.

---

## Features

- **Plain-English machine definition** — a local Ollama model extracts parameters from a paragraph. If Ollama is offline, a deterministic keyword parser takes over, so the app never crashes.
- **Schema-agnostic generator** — vectorized and reproducible (seeded), scales to 1,000,000 records.
- **Edge-case engine** — four failure scenarios: *Boundary values*, *Missing or corrupted data*, *Combined equipment failure*, *Network outage*.
- **Domain templates** — physics and business rules for IoT / Manufacturing, Logistics, Finance, Healthcare and E-commerce.
- **Privacy evaluator** — exact-match detection, k-anonymity and PII leak checks.
- **Quality validator** — KS tests and range checks against the machine profile.
- **Predictive evaluation** — RandomForest trained WITH vs. WITHOUT edge cases to quantify anomaly-detection gain.
- **What-if analysis** — re-run a generation with different size, edge-case frequency or scenario.
- **Export** — CSV, JSON or Parquet.

## Repository Structure

```
.
├── src/
│   ├── backend/            # FastAPI app
│   │   ├── llm/            #   Ollama client + keyword fallback parser
│   │   ├── main.py         #   REST API routes
│   │   ├── models.py       #   Pydantic data contract & /api/config-spec
│   │   ├── services.py     #   Generation & analytics orchestrator
│   │   ├── database.py     #   SQLite persistence (profiles, runs)
│   │   └── requirements.txt
│   ├── ml/                 # Data + ML engine
│   │   ├── generator.py        # Schema-agnostic vectorized generator
│   │   ├── edge_cases.py       # 4 failure scenarios
│   │   ├── domain_templates.py # 5 domains
│   │   ├── privacy.py          # Privacy evaluator
│   │   ├── validation.py       # Quality validator
│   │   ├── pipeline.py         # Cleaning, feature engineering, trends
│   │   └── predictive.py       # WITH vs WITHOUT edge-case model
│   └── frontend/           # Next.js 14 + TypeScript + Tailwind UI
├── scripts/                # setup / run / test helpers (sh, bat, ps1)
├── tests/                  # pytest suite (phases 0–14)
├── docs/                   # architecture, API docs, benchmarks, model report
├── data/samples/           # pre-generated sample datasets
├── docker-compose.yml
├── Makefile
├── .env.example
└── LICENSE
```

## Quick Start

### Option 1 — Docker

```bash
cp .env.example .env
docker-compose up --build
```

- Frontend: <http://localhost:3000>
- Backend API: <http://localhost:8000>

### Option 2 — Scripts (no Docker)

**Linux / macOS**
```bash
./scripts/setup.sh        # one-time: venv, dependencies, .env
./scripts/run.sh          # backend + built-in dashboard on :8000
./scripts/run.sh --all    # also start the Next.js frontend on :3000
```

**Windows**
```powershell
pip install -r src\backend\requirements.txt
.\scripts\run.ps1         # or scripts\run.bat
```

### Option 3 — Manual / Make

```bash
make setup      # install backend + frontend dependencies
make backend    # http://localhost:8000
make frontend   # http://localhost:3000
```

Requirements: **Python 3.11**, **Node.js 18+** (frontend only), and optionally **Docker** and **Ollama**.

## Local AI Setup (Ollama)

SynthEdge uses a free, offline LLM through [Ollama](https://ollama.com) to turn a paragraph into structured machine parameters.

```bash
ollama pull qwen2.5-coder:7b
ollama list              # confirm it is installed
```

Configure `.env` (copy from `.env.example`):

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
OLLAMA_TIMEOUT_SECONDS=60
```

- If `OLLAMA_MODEL` is empty, the first installed instruct/chat model is auto-selected.
- If Ollama is offline, the model is missing, or a request times out, the **Define Machine** page shows *"Local AI offline, using basic parser"* and falls back to `src/backend/llm/keyword_parser.py`.

## Usage Flow

1. **Define** — describe your machine in plain English.
2. **Configure** — choose domain, record count, edge-case frequency and scenario, seed, and output format.
3. **Results** — review quality and privacy reports, the WITH vs. WITHOUT model comparison, and download the dataset.

## API Overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/config-spec` | Data contract / configuration spec |
| GET | `/api/llm-status` | Is local AI online? |
| POST | `/api/parse-machine` | Paragraph → machine parameters |
| POST / GET | `/api/machines`, `/api/machines/{id}` | Save / list / fetch machine profiles |
| POST | `/api/generate` | Generate a dataset |
| GET | `/api/runs`, `/api/runs/{id}` | List / fetch runs |
| POST | `/api/validate` | Quality and privacy validation |
| POST | `/api/whatif` | Re-run with modified settings |
| GET | `/api/download/{run_id}` | Download generated dataset |

Full details: [`docs/api_documentation.md`](docs/api_documentation.md). Architecture: [`docs/architecture.md`](docs/architecture.md).

## Performance

| Records | Generation time | Memory (RSS) | Throughput |
|---|---|---|---|
| 1,000 | 0.006 s | 103.5 MB | 166,667 rec/s |
| 10,000 | 0.004 s | 105.3 MB | 2,500,000 rec/s |
| 100,000 | 0.025 s | 115.3 MB | 4,000,000 rec/s |
| **1,000,000** | **0.217 s** | **189.5 MB** | **4,608,295 rec/s** |

See [`docs/scalability_benchmark.md`](docs/scalability_benchmark.md).

## Testing

```bash
./scripts/test.sh        # or: make test
```

The suite in `tests/` is organized by build phase (setup, data contract, parser, generator, edge cases, domains, privacy, validation, pipeline, predictive model, API, frontend, scalability, hardening).

## Roadmap

- RAG over uploaded domain documents to ground machine definitions
- Self-hosted deployment on a VPS with a production-grade reverse proxy
- Additional domains and edge-case scenarios

## Contributing

Issues and pull requests are welcome. Please run `make test` before submitting a PR.

## License

Released under the [MIT License](LICENSE).
