import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.models import (
    MachineProfile,
    Parameter,
    NumberConfig,
    CategoryConfig,
    BooleanConfig,
    TextConfig,
    DatetimeConfig,
    GenerationConfig,
    get_config_spec
)
from backend.main import app

client = TestClient(app)


def test_valid_machine_profile():
    p1 = Parameter(name="temperature", type="number", number=NumberConfig(min=0.0, max=100.0, unit="°C"))
    p2 = Parameter(name="status", type="category", category=CategoryConfig(values=["normal", "warning", "critical"]))
    p3 = Parameter(name="is_active", type="boolean", boolean=BooleanConfig(true_share=85.0))

    mp = MachineProfile(
        name="Water Pump Station",
        description="A real-time monitored water pumping station.",
        suggested_domain="IoT / Manufacturing",
        domain="IoT / Manufacturing",
        parameters=[p1, p2, p3]
    )
    assert mp.name == "Water Pump Station"
    assert len(mp.parameters) == 3


def test_duplicate_parameter_names_case_insensitive():
    p1 = Parameter(name="Temperature", type="number", number=NumberConfig(min=0.0, max=100.0))
    p2 = Parameter(name="temperature", type="number", number=NumberConfig(min=10.0, max=50.0))

    with pytest.raises(ValidationError) as excinfo:
        MachineProfile(name="Fail Profile", parameters=[p1, p2])
    assert "Duplicate parameter name" in str(excinfo.value)


def test_number_min_greater_than_or_equal_max():
    with pytest.raises(ValidationError) as excinfo:
        NumberConfig(min=100.0, max=50.0)
    assert "min (100.0) must be strictly less than max (50.0)" in str(excinfo.value)

    with pytest.raises(ValidationError):
        NumberConfig(min=50.0, max=50.0)


def test_category_fewer_than_2_values():
    with pytest.raises(ValidationError) as excinfo:
        CategoryConfig(values=["single_value"])
    assert "at least 2" in str(excinfo.value)


def test_boolean_true_share_out_of_range():
    with pytest.raises(ValidationError):
        BooleanConfig(true_share=-5.0)

    with pytest.raises(ValidationError):
        BooleanConfig(true_share=120.0)

    # Valid bounds
    b1 = BooleanConfig(true_share=0.0)
    b2 = BooleanConfig(true_share=100.0)
    assert b1.true_share == 0.0
    assert b2.true_share == 100.0


def test_empty_parameters_list():
    with pytest.raises(ValidationError) as excinfo:
        MachineProfile(name="Empty Profile", parameters=[])
    assert "at least one parameter" in str(excinfo.value)


def test_generation_config_bounds():
    # Valid config
    gc = GenerationConfig(machine_id="test-id", num_records=10000, edge_case_frequency=5.0)
    assert gc.num_records == 10000
    assert gc.edge_case_frequency == 5.0

    # Invalid num_records (< 100 or > 100,000)
    with pytest.raises(ValidationError):
        GenerationConfig(machine_id="test-id", num_records=50)

    with pytest.raises(ValidationError):
        GenerationConfig(machine_id="test-id", num_records=200000)

    # Invalid edge_case_frequency (< 1 or > 20)
    with pytest.raises(ValidationError):
        GenerationConfig(machine_id="test-id", edge_case_frequency=0.5)

    with pytest.raises(ValidationError):
        GenerationConfig(machine_id="test-id", edge_case_frequency=25.0)


def test_get_config_spec_endpoint():
    response = client.get("/api/config-spec")
    assert response.status_code == 200
    data = response.json()
    assert "machine_profile_schema" in data
    assert "parameter_schema" in data
    assert "generation_config_schema" in data
    assert "domains" in data
    assert "scenarios" in data
    assert "defaults" in data
    assert data["defaults"]["num_records"] == 10000
