import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_full_api_generation_and_retrieval_flow():
    # 1. Create a machine profile
    mac_payload = {
        "name": "Full API Test Pump",
        "description": "Industrial pump with temperature and pressure sensors.",
        "suggested_domain": "IoT / Manufacturing",
        "domain": "IoT / Manufacturing",
        "parameters": [
            {
                "name": "temperature",
                "type": "number",
                "number": {"min": 10.0, "max": 90.0, "unit": "°C"}
            },
            {
                "name": "pressure",
                "type": "number",
                "number": {"min": 1.0, "max": 10.0, "unit": "bar"}
            }
        ]
    }
    res_mac = client.post("/api/machines", json=mac_payload)
    assert res_mac.status_code == 201
    machine_id = res_mac.json()["id"]

    # 2. POST /api/generate
    gen_config = {
        "machine_id": machine_id,
        "num_records": 500,
        "edge_case_frequency": 5.0,
        "scenario": "Combined equipment failure",
        "seed": 42,
        "output_format": "csv"
    }
    res_gen = client.post("/api/generate", json=gen_config)
    assert res_gen.status_code == 201
    gen_data = res_gen.json()
    assert "run_id" in gen_data
    run_id = gen_data["run_id"]
    assert gen_data["num_records"] == 500
    assert gen_data["total_edge_cases"] == 25  # round(500 * 0.05)
    assert "quality_report" in gen_data
    assert "privacy_report" in gen_data
    assert "predictive_report" in gen_data
    assert len(gen_data["preview_rows"]) <= 20

    # 3. GET /api/runs
    res_runs = client.get("/api/runs")
    assert res_runs.status_code == 200
    runs_list = res_runs.json()
    run_ids = [r["run_id"] for r in runs_list]
    assert run_id in run_ids

    # 4. GET /api/runs/{run_id}
    res_get_run = client.get(f"/api/runs/{run_id}")
    assert res_get_run.status_code == 200
    assert res_get_run.json()["run_id"] == run_id

    # 5. POST /api/validate
    res_val = client.post("/api/validate", json=mac_payload)
    assert res_val.status_code == 200
    assert "quality_report" in res_val.json()

    # 6. GET /api/download/{run_id}
    res_dl = client.get(f"/api/download/{run_id}")
    assert res_dl.status_code == 200
    assert len(res_dl.content) > 0

    # 7. POST /api/whatif
    whatif_payload = {
        "run_id": run_id,
        "edge_case_frequency": 10.0,
        "scenario": "Boundary values"
    }
    res_whatif = client.post("/api/whatif", json=whatif_payload)
    assert res_whatif.status_code == 200
    whatif_data = res_whatif.json()
    assert whatif_data["total_edge_cases"] == 50  # round(500 * 0.10)
    assert whatif_data["scenario"] == "Boundary values"
