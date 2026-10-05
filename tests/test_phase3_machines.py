import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_create_and_get_machine_profile():
    payload = {
        "name": "ATM Terminal System",
        "description": "Smart ATM machine handling cash withdrawals and balances.",
        "suggested_domain": "Finance",
        "domain": "Finance",
        "parameters": [
            {
                "name": "withdrawal_amount",
                "type": "number",
                "number": {"min": 20.0, "max": 1000.0, "unit": "USD", "distribution": "normal"}
            },
            {
                "name": "card_type",
                "type": "category",
                "category": {"values": ["visa", "mastercard", "amex"]}
            },
            {
                "name": "is_receipt_printed",
                "type": "boolean",
                "boolean": {"true_share": 75.0}
            }
        ]
    }

    # 1. Create machine profile
    res_create = client.post("/api/machines", json=payload)
    assert res_create.status_code == 201
    created_data = res_create.json()
    assert "id" in created_data
    machine_id = created_data["id"]
    assert created_data["name"] == "ATM Terminal System"
    assert len(created_data["parameters"]) == 3

    # 2. Get machine profile by ID
    res_get = client.get(f"/api/machines/{machine_id}")
    assert res_get.status_code == 200
    fetched_data = res_get.json()
    assert fetched_data["id"] == machine_id
    assert fetched_data["domain"] == "Finance"
    assert fetched_data["parameters"][0]["name"] == "withdrawal_amount"

    # 3. List machine profiles
    res_list = client.get("/api/machines")
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert len(list_data) >= 1
    ids = [m["id"] for m in list_data]
    assert machine_id in ids


def test_get_nonexistent_machine_returns_404():
    res = client.get("/api/machines/nonexistent-id-99999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"]


def test_create_invalid_machine_returns_400():
    invalid_payload = {
        "name": "Broken Machine",
        "parameters": [
            {
                "name": "temp",
                "type": "number",
                "number": {"min": 100.0, "max": 50.0}  # min >= max
            }
        ]
    }
    res = client.post("/api/machines", json=invalid_payload)
    assert res.status_code == 422 or res.status_code == 400
