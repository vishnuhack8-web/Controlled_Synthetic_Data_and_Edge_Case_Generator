import json
import pytest
import requests
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.llm.keyword_parser import parse_description_with_keywords
from backend.llm.ollama_client import OllamaClient

client = TestClient(app)


# 1. Empty paragraph validation
def test_empty_paragraph_validation():
    with pytest.raises(ValueError) as exc:
        parse_description_with_keywords("")
    assert "Describe your machine first" in str(exc.value)

    res = client.post("/api/parse-machine", json={"description": "  "})
    assert res.status_code == 400
    assert "Describe your machine first" in res.json()["detail"]


# 2. Too-short paragraph validation
def test_too_short_paragraph_validation():
    with pytest.raises(ValueError) as exc:
        parse_description_with_keywords("Water pump sensor")
    assert "Add a little more detail so we can find the inputs" in str(exc.value)

    res = client.post("/api/parse-machine", json={"description": "Water pump sensor"})
    assert res.status_code == 400
    assert "Add a little more detail so we can find the inputs" in res.json()["detail"]


# 3. Network status vs machine status distinction (Rule 8/10)
def test_network_status_vs_machine_status_distinction():
    desc_net = "This smart device tracks network status connectivity and wifi signal strength periodically."
    res_net = parse_description_with_keywords(desc_net)
    names_net = [p.name for p in res_net["parameters"]]
    assert "network_status" in names_net

    desc_mac = "This industrial machine monitors operational machine status and motor speed in real time."
    res_mac = parse_description_with_keywords(desc_mac)
    names_mac = [p.name for p in res_mac["parameters"]]
    assert "machine_status" in names_mac


# 4. Paragraph with no specific inputs (default fallback parameters)
def test_paragraph_with_no_inputs():
    desc = "This is a generic mystery box system that performs abstract operational routines."
    res = parse_description_with_keywords(desc)
    assert len(res["parameters"]) >= 2
    assert res["using_fallback"] is True


# 5. Mock Ollama - Valid JSON response
@patch("requests.get")
@patch("requests.post")
def test_ollama_client_valid_json(mock_post, mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "models": [{"name": "qwen2.5-coder:7b"}]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": json.dumps({
                "name": "Water Pump Station",
                "suggested_domain": "IoT / Manufacturing",
                "parameters": [
                    {
                        "name": "temperature",
                        "type": "number",
                        "number": {"min": 10.0, "max": 90.0, "unit": "°C", "distribution": "normal"}
                    },
                    {
                        "name": "status",
                        "type": "category",
                        "category": {"values": ["idle", "running", "error"]}
                    }
                ]
            })
        }
    }
    mock_post.return_value = mock_response

    ollama = OllamaClient()
    result = ollama.parse_machine("A high pressure water pump with a temperature sensor and status mode indicators.")
    assert result["using_fallback"] is False
    assert result["model_used"] == "qwen2.5-coder:7b"
    assert len(result["parameters"]) == 2
    assert result["parameters"][0]["name"] == "temperature"


# 6. Mock Ollama - Reasoning model with <think>...</think> tags
def test_strip_think_tags():
    ollama = OllamaClient()
    raw = "<think>\nLet us analyze the inputs carefully.\nUser mentioned temperature.\n</think>\n{\"name\": \"Pump\", \"suggested_domain\": \"IoT / Manufacturing\", \"parameters\": []}"
    clean = ollama._strip_think_tags(raw)
    assert "<think>" not in clean
    assert clean.startswith('{"name"')


# 7. Mock Ollama - Invalid JSON (retries once, then falls back)
@patch("requests.get")
@patch("requests.post")
def test_ollama_client_invalid_json_fallback(mock_post, mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "models": [{"name": "qwen2.5-coder:7b"}]
    }

    mock_bad_resp = MagicMock()
    mock_bad_resp.status_code = 200
    mock_bad_resp.json.return_value = {"message": {"content": "INVALID NON JSON TEXT"}}
    mock_post.return_value = mock_bad_resp

    ollama = OllamaClient()
    res = ollama.parse_machine("Water pump station with temperature and pressure sensors operating continuously.")
    assert res["using_fallback"] is True
    assert "invalid output" in res.get("notice", "")


# 8. Mock Ollama - Ollama Not Running (Connection Refused)
@patch("requests.get", side_effect=requests.exceptions.ConnectionError("Connection refused"))
def test_ollama_client_not_running(mock_get):
    ollama = OllamaClient()
    res = ollama.parse_machine("Water pump station with temperature and pressure sensors operating continuously.")
    assert res["using_fallback"] is True
    assert "offline" in res.get("notice", "")


# 9. Mock Ollama - Model Missing
@patch("requests.get")
def test_ollama_client_model_missing(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"models": []}

    ollama = OllamaClient()
    res = ollama.parse_machine("Water pump station with temperature and pressure sensors operating continuously.")
    assert res["using_fallback"] is True


# 10. Mock Ollama - Timeout
@patch("requests.get")
@patch("requests.post", side_effect=requests.exceptions.Timeout("Read timeout"))
def test_ollama_client_timeout(mock_post, mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"models": [{"name": "qwen2.5-coder:7b"}]}

    ollama = OllamaClient()
    res = ollama.parse_machine("Water pump station with temperature and pressure sensors operating continuously.")
    assert res["using_fallback"] is True


# 11. Integration Test with REAL Local Ollama
def test_real_ollama_integration():
    """
    Runs ONLY when local Ollama is reachable on port 11434.
    Tests real model output for Water Pump and Vending Machine paragraphs.
    """
    ollama = OllamaClient()
    status = ollama.get_status()

    if not status["reachable"] or not status["models_installed"]:
        pytest.skip("Local Ollama server is not reachable on port 11434. Skipping integration test.")

    print(f"\n=======================================================")
    print(f"[OLLAMA REAL INTEGRATION TEST]")
    print(f"Models installed: {status['models_installed']}")
    print(f"Model in use: {status['model_in_use']}")
    print(f"=======================================================\n")

    water_pump_desc = "A high-capacity industrial water pump station that monitors temperature (0-100 °C), pressure (1-10 bar), flow rate (0-500 L/min), operational mode (idle, running, error), emergency stop button state, and records timestamps every 5 seconds."
    vending_machine_desc = "A smart vending machine that tracks item inventory stock level (0-100 items), internal temperature (2-10 °C), payment method (cash, credit_card, mobile_pay), network connectivity status (online, offline), and door sensor."

    res_pump = ollama.parse_machine(water_pump_desc)
    print("--- REAL PARSED WATER PUMP OUTPUT ---")
    print(json.dumps(res_pump, indent=2))

    res_vending = ollama.parse_machine(vending_machine_desc)
    print("\n--- REAL PARSED VENDING MACHINE OUTPUT ---")
    print(json.dumps(res_vending, indent=2))

    assert "parameters" in res_pump
    assert len(res_pump["parameters"]) > 0
    assert "parameters" in res_vending
    assert len(res_vending["parameters"]) > 0
