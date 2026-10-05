import pytest
import pandas as pd
import numpy as np

from backend.models import (
    MachineProfile,
    Parameter,
    NumberConfig,
    CategoryConfig,
    BooleanConfig,
    TextConfig,
    DatetimeConfig
)
from ml.generator import SyntheticDataGenerator
from ml.edge_cases import EdgeCaseEngine


# Helper fixtures for 3 distinct schemas
def get_iot_sensors_profile():
    return MachineProfile(
        name="IoT Sensors Profile",
        parameters=[
            Parameter(name="temp", type="number", number=NumberConfig(min=10.0, max=90.0, unit="°C")),
            Parameter(name="pressure", type="number", number=NumberConfig(min=1.0, max=10.0, unit="bar")),
            Parameter(name="status", type="category", category=CategoryConfig(values=["normal", "warning", "error"])),
            Parameter(name="timestamp", type="datetime", datetime=DatetimeConfig(interval="every 5 seconds"))
        ]
    )


def get_atm_transactions_profile():
    return MachineProfile(
        name="ATM Transactions Profile",
        suggested_domain="Finance",
        parameters=[
            Parameter(name="withdrawal_amount", type="number", number=NumberConfig(min=20.0, max=1000.0, unit="USD")),
            Parameter(name="card_type", type="category", category=CategoryConfig(values=["visa", "mastercard"])),
            Parameter(name="network_status", type="category", category=CategoryConfig(values=["online", "offline"])),
            Parameter(name="is_receipt_printed", type="boolean", boolean=BooleanConfig(true_share=80.0))
        ]
    )


def get_custom_user_profile():
    return MachineProfile(
        name="Custom User Profile",
        parameters=[
            Parameter(name="fill_level", type="number", number=NumberConfig(min=0.0, max=100.0, unit="%")),
            Parameter(name="power_draw", type="number", number=NumberConfig(min=10.0, max=500.0, unit="W")),
            Parameter(name="alarm_active", type="boolean", boolean=BooleanConfig(true_share=5.0)),
            Parameter(name="device_token", type="text", text=TextConfig())
        ]
    )


def test_edge_case_exact_counts_min_default_max_frequencies():
    profile = get_iot_sensors_profile()
    gen = SyntheticDataGenerator(seed=42)
    engine = EdgeCaseEngine()
    df_base = gen.generate(profile, num_records=1000, seed=42)

    for freq in [1.0, 5.0, 20.0]:
        df_edge = engine.inject_edge_cases(df_base, profile, scenario="Combined equipment failure", frequency=freq, seed=42)
        expected_count = int(round(1000 * (freq / 100.0)))
        actual_count = int((df_edge["is_edge_case"] == 1).sum())
        assert actual_count == expected_count, f"Expected {expected_count} edge cases for {freq}%, got {actual_count}"


def test_edge_cases_across_3_distinct_schemas():
    generator = SyntheticDataGenerator(seed=100)
    engine = EdgeCaseEngine()

    profiles = [
        ("IoT Sensors", get_iot_sensors_profile()),
        ("ATM Transactions", get_atm_transactions_profile()),
        ("Custom User Schema", get_custom_user_profile())
    ]

    for name, prof in profiles:
        df_base = generator.generate(prof, num_records=500, seed=100)
        df_edge = engine.inject_edge_cases(df_base, prof, scenario="Boundary values", frequency=10.0, seed=100)
        expected_count = int(round(500 * 0.10))
        actual_count = int((df_edge["is_edge_case"] == 1).sum())
        assert actual_count == expected_count, f"Schema {name} failed: expected {expected_count}, got {actual_count}"
        assert "is_edge_case" in df_edge.columns
        assert "edge_case_type" in df_edge.columns


def test_all_4_scenarios_injection():
    profile = get_iot_sensors_profile()
    gen = SyntheticDataGenerator(seed=200)
    engine = EdgeCaseEngine()
    df_base = gen.generate(profile, num_records=400, seed=200)

    for scenario in engine.SCENARIOS:
        df_edge = engine.inject_edge_cases(df_base, profile, scenario=scenario, frequency=5.0, seed=200)
        assert (df_edge["is_edge_case"] == 1).sum() == 20
        edge_rows = df_edge[df_edge["is_edge_case"] == 1]
        assert (edge_rows["edge_case_type"] == scenario).all()
