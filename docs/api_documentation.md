# REST API Documentation

Base URL: `http://localhost:8000`

---

## Endpoints Summary

### 1. `GET /api/health`
Returns backend health status.
**Response**:
```json
{
  "status": "ok",
  "service": "synthetic-data-platform-backend",
  "version": "1.0.0"
}
```

---

### 2. `GET /api/config-spec`
Serves the single source of truth configuration schema contract for frontend landing page and Ollama output schema.
**Response**: Contains `machine_profile_schema`, `parameter_schema`, `generation_config_schema`, `domains`, `scenarios`, and default bounds.

---

### 3. `GET /api/llm-status`
Returns status of local Ollama connection and model selection.
**Response**:
```json
{
  "reachable": true,
  "models_installed": ["qwen2.5-coder:7b", "gemma4:e4b"],
  "model_in_use": "qwen2.5-coder:7b",
  "using_fallback": false
}
```

---

### 4. `POST /api/parse-machine`
Extracts parameter list from text paragraph using local Ollama model (with keyword parser fallback).
**Request Body**:
```json
{
  "description": "A water pump station with temperature (0-100 C), pressure (1-10 bar), and status mode."
}
```
**Response**: `MachineProfile` parameters and suggested domain.

---

### 5. `POST /api/machines`
Saves a `MachineProfile` into SQLite storage.
**Response**: Saved `MachineProfile` object with unique `id`.

---

### 6. `GET /api/machines` & `GET /api/machines/{machine_id}`
Lists saved machine profiles or retrieves a specific profile by ID for shareable links.

---

### 7. `POST /api/generate`
Runs end-to-end dataset generation, edge-case injection, quality validation, privacy evaluation, and predictive analytics.
**Request Body**:
```json
{
  "machine_id": "uuid-string",
  "num_records": 10000,
  "edge_case_frequency": 5.0,
  "scenario": "Combined equipment failure",
  "seed": 42,
  "output_format": "csv"
}
```
**Response**: Full run result payload including `quality_report`, `privacy_report`, `predictive_report`, `preview_rows`, and `edge_case_breakdown`.

---

### 8. `GET /api/runs` & `GET /api/runs/{run_id}`
Lists historical runs or fetches full metadata for a specific run ID.

---

### 9. `POST /api/validate`
Validates a machine profile or sample dataset against contract and privacy rules.

---

### 10. `GET /api/download/{run_id}`
Downloads generated dataset file in requested format (`csv`, `json`, `parquet`).

---

### 11. `POST /api/whatif`
Re-runs generation scenario on an existing machine run with updated parameters.
