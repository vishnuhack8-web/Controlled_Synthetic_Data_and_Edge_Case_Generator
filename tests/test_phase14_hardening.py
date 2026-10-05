import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_full_e2e_flow_landing_to_download_with_fallback():
    # 1. Landing page config spec check
    res_spec = client.get("/api/config-spec")
    assert res_spec.status_code == 200
    assert "defaults" in res_spec.json()

    # 2. Define machine - Analyze text with Ollama offline (Testing Fallback Parser)
    with patch("requests.get", side_effect=Exception("Ollama offline")):
        res_parse = client.post("/api/parse-machine", json={
            "description": "A high pressure water pump station with temperature (0-100 °C), pressure gauge, motor speed, and network status."
        })
        assert res_parse.status_code == 200
        parsed_data = res_parse.json()
        assert parsed_data["using_fallback"] is True
        assert len(parsed_data["parameters"]) >= 2

    # 3. Edit range and add custom parameter
    params = parsed_data["parameters"]
    # Edit a range
    params[0]["number"] = {"min": 5.0, "max": 95.0, "unit": "°C", "distribution": "normal"}
    # Add a custom parameter
    params.append({
        "name": "custom_vibration",
        "type": "number",
        "number": {"min": 0.1, "max": 15.0, "unit": "mm/s", "distribution": "uniform"}
    })

    # Save Machine Profile
    mac_payload = {
        "name": "E2E Hardened Water Pump",
        "description": "Full E2E workflow machine.",
        "suggested_domain": "IoT / Manufacturing",
        "domain": "IoT / Manufacturing",
        "parameters": params
    }
    res_mac = client.post("/api/machines", json=mac_payload)
    assert res_mac.status_code == 201
    machine_id = res_mac.json()["id"]

    # 4. Configure & Generate Dataset
    gen_payload = {
        "machine_id": machine_id,
        "num_records": 1000,
        "edge_case_frequency": 5.0,
        "scenario": "Boundary values",
        "seed": 12345,
        "output_format": "csv"
    }
    res_gen = client.post("/api/generate", json=gen_payload)
    assert res_gen.status_code == 201
    gen_res = res_gen.json()
    run_id = gen_res["run_id"]
    assert gen_res["total_edge_cases"] == 50  # round(1000 * 0.05)

    # 5. Reproducibility test: Same seed twice produces exact same output
    res_gen2 = client.post("/api/generate", json=gen_payload)
    assert res_gen2.status_code == 201
    gen_res2 = res_gen2.json()
    assert gen_res["quality_report"]["quality_score"] == gen_res2["quality_report"]["quality_score"]

    # 6. Invalid Config Rejections
    bad_config = {
        "machine_id": machine_id,
        "num_records": 10,  # Below min 100 limit
        "edge_case_frequency": 5.0
    }
    res_bad = client.post("/api/generate", json=bad_config)
    assert res_bad.status_code == 422 or res_bad.status_code == 400

    # 7. Results Dashboard & Download
    res_run_get = client.get(f"/api/runs/{run_id}")
    assert res_run_get.status_code == 200

    res_dl = client.get(f"/api/download/{run_id}")
    assert res_dl.status_code == 200
    assert len(res_dl.content) > 0
