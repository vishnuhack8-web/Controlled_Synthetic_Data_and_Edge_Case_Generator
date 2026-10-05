import pytest
import requests
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_backend_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "synthetic-data-platform-backend"

def test_llm_status_endpoint():
    response = client.get("/api/llm-status")
    assert response.status_code == 200
    data = response.json()
    assert "reachable" in data
    assert "models_installed" in data
    assert "model_in_use" in data
    assert "using_fallback" in data

def test_direct_ollama_tags():
    """Check direct HTTP connectivity to http://localhost:11434/api/tags."""
    try:
        res = requests.get("http://localhost:11434/api/tags", timeout=3)
        if res.status_code == 200:
            models = [m.get("name") for m in res.json().get("models", [])]
            print(f"\n[OLLAMA ONLINE] Installed models: {models}")
        else:
            print(f"\n[OLLAMA CONNECTED BUT STATUS {res.status_code}]")
    except Exception as err:
        print(f"\n[OLLAMA OFFLINE OR UNREACHABLE AT PORT 11434]: {err}")
