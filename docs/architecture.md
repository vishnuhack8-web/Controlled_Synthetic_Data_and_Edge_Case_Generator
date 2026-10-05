# System Architecture & Technical Specification

The **SynthEdge** platform is built as a schema-agnostic, privacy-preserving synthetic data and edge-case generation system powered by a local Ollama LLM (`qwen2.5-coder:7b`) for machine paragraph extraction and a high-performance Python ML engine for data synthesis.

---

## Mermaid Architecture Diagram

```mermaid
flowchart TD
    User([User / Team Member]) -->|1. Describe Machine Paragraph| Frontend[Next.js TypeScript Frontend]
    Frontend -->|POST /api/parse-machine| FastAPI[FastAPI Backend Server]
    
    subgraph Local AI Extraction
        FastAPI -->|Check Tags GET /api/tags| OllamaClient[Ollama Client / src/backend/llm/ollama_client.py]
        OllamaClient -->|POST /api/chat structured JSON| LocalOllama[Local Ollama Server - qwen2.5-coder:7b]
        OllamaClient -->|Fallback if offline| KeywordParser[Keyword Fallback Parser / src/backend/llm/keyword_parser.py]
    end

    subgraph Data Contract & Persistence
        FastAPI -->|Store / Retrieve Machine Profiles| SQLite[(SQLite Database - data/app.db)]
        FastAPI -->|GET /api/config-spec| SingleSourceContract[Central Data Contract - src/backend/models.py]
    end

    subgraph Schema-Agnostic Generation Pipeline
        FastAPI -->|POST /api/generate| DataGenerator[Synthetic Data Generator / src/ml/generator.py]
        DataGenerator -->|Layer Business Rules| DomainTemplates[Domain Templates Engine / src/ml/domain_templates.py]
        DomainTemplates -->|Inject Failures| EdgeCaseEngine[Edge Case Engine / src/ml/edge_cases.py]
        EdgeCaseEngine -->|Clean & Feature Eng| ProcessingPipeline[Data Processing Pipeline / src/ml/pipeline.py]
    end

    subgraph Validation & Predictive Analytics
        ProcessingPipeline -->|Privacy Scan| PrivacyEvaluator[Privacy Evaluator / src/ml/privacy.py]
        ProcessingPipeline -->|Quality Validation| QualityValidator[Data Quality Validator / src/ml/validation.py]
        ProcessingPipeline -->|Train Failure Model| PredictiveEngine[Predictive Analytics Engine / src/ml/predictive.py]
    end

    PredictiveEngine -->|Export CSV / JSON / Parquet| RunStorage[Run File Storage - data/runs/]
    RunStorage -->|Serve Preview & Downloads| Frontend
```

---

## Engine Modules Breakdown

1. **Central Data Contract (`src/backend/models.py`)**:
   Single source of truth Pydantic models for `MachineProfile`, `Parameter`, `GenerationConfig`, and single source endpoint `/api/config-spec`.

2. **Ollama Machine Parser (`src/backend/llm/ollama_client.py`)**:
   Queries local Ollama `/api/chat` with structured Pydantic JSON schema, strips `<think>` reasoning tags, retries once on parse errors, and falls back gracefully to `keyword_parser.py` if Ollama is stopped.

3. **Core Schema-Agnostic Data Generator (`src/ml/generator.py`)**:
   Vectorized NumPy/pandas data generator supporting all 5 parameter types (`number`, `category`, `boolean`, `text`, `datetime`), distributions (`uniform`, `normal`, `exponential`), chunked memory allocation up to 1M records, and exact seed reproducibility.

4. **Edge-Case Engine (`src/ml/edge_cases.py`)**:
   Schema-agnostic anomaly injector supporting 4 failure scenarios: *Boundary values*, *Missing or corrupted data*, *Combined equipment failure*, *Network outage*, with exact `round(records x frequency)` injection.

5. **Domain Templates Engine (`src/ml/domain_templates.py`)**:
   Layers statistical physics and business rules across 5 domains: *IoT / Manufacturing*, *Logistics*, *Finance*, *Healthcare*, *E-commerce*.

6. **Privacy Evaluator (`src/ml/privacy.py`)**:
   Evaluates exact matches, nearest-neighbor Euclidean distance matrix, k-anonymity group size, and regex PII scans (SSN, credit card, email, phone).

7. **Data Quality Validator (`src/ml/validation.py`)**:
   Evaluates schema compliance, completeness, range satisfaction, and Kolmogorov-Smirnov (KS) statistical goodness-of-fit.

8. **Predictive Analytics Engine (`src/ml/predictive.py`)**:
   Trains scikit-learn RandomForest classifiers WITH vs WITHOUT edge cases to quantify anomaly detection F1 and recall gains.
