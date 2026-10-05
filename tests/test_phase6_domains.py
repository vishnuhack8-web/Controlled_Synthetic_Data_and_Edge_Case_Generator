import pytest
import pandas as pd
import numpy as np

from backend.models import (
    MachineProfile,
    Parameter,
    NumberConfig,
    CategoryConfig,
    BooleanConfig
)
from ml.generator import SyntheticDataGenerator
from ml.domain_templates import DomainTemplateEngine


def test_iot_domain_thermal_speed_correlation():
    p_speed = Parameter(name="motor_speed", type="number", number=NumberConfig(min=500.0, max=3500.0, unit="RPM"))
    p_temp = Parameter(name="temperature", type="number", number=NumberConfig(min=20.0, max=100.0, unit="°C"))
    p_vib = Parameter(name="vibration", type="number", number=NumberConfig(min=0.1, max=10.0, unit="mm/s"))
    p_status = Parameter(name="status", type="category", category=CategoryConfig(values=["running", "warning", "error"]))

    profile = MachineProfile(name="IoT Engine", domain="IoT / Manufacturing", parameters=[p_speed, p_temp, p_vib, p_status])

    gen = SyntheticDataGenerator(seed=42)
    df_raw = gen.generate(profile, num_records=2000, seed=42)

    engine = DomainTemplateEngine()
    df_domain = engine.apply_domain_rules(df_raw, profile, domain="IoT / Manufacturing")

    # Check that correlation between motor_speed and temperature increased
    corr_raw = df_raw["motor_speed"].corr(df_raw["temperature"])
    corr_domain = df_domain["motor_speed"].corr(df_domain["temperature"])

    assert corr_domain > corr_raw, f"Expected domain correlation ({corr_domain:.3f}) > raw correlation ({corr_raw:.3f})"
    assert (df_domain["temperature"] >= 20.0).all() and (df_domain["temperature"] <= 100.0).all()


def test_logistics_domain_weight_speed_drag():
    p_weight = Parameter(name="cargo_weight", type="number", number=NumberConfig(min=100.0, max=5000.0, unit="kg"))
    p_speed = Parameter(name="vehicle_speed", type="number", number=NumberConfig(min=10.0, max=120.0, unit="km/h"))

    profile = MachineProfile(name="Logistics Fleet", domain="Logistics", parameters=[p_weight, p_speed])
    gen = SyntheticDataGenerator(seed=123)
    df_raw = gen.generate(profile, num_records=1500, seed=123)

    engine = DomainTemplateEngine()
    df_domain = engine.apply_domain_rules(df_raw, profile, domain="Logistics")

    # Negative correlation expected (heavy cargo -> lower speed)
    corr_domain = df_domain["cargo_weight"].corr(df_domain["vehicle_speed"])
    assert corr_domain < 0.0, f"Expected negative weight-speed correlation, got {corr_domain:.3f}"


def test_finance_domain_high_amount_risk_flag():
    p_amt = Parameter(name="transaction_amount", type="number", number=NumberConfig(min=10.0, max=10000.0, unit="USD"))
    p_flag = Parameter(name="fraud_flag", type="boolean", boolean=BooleanConfig(true_share=5.0))

    profile = MachineProfile(name="Bank ATM", domain="Finance", parameters=[p_amt, p_flag])
    gen = SyntheticDataGenerator(seed=999)
    df_raw = gen.generate(profile, num_records=1000, seed=999)

    engine = DomainTemplateEngine()
    df_domain = engine.apply_domain_rules(df_raw, profile, domain="Finance")

    # High amount rows (> 85th percentile) should have fraud_flag == True
    high_amt_mask = df_domain["transaction_amount"] > (10.0 + (10000.0 - 10.0) * 0.85)
    high_amt_rows = df_domain[high_amt_mask]
    if len(high_amt_rows) > 0:
        assert (high_amt_rows["fraud_flag"] == True).all()


def test_healthcare_domain_vital_correlations():
    p_hr = Parameter(name="heart_rate", type="number", number=NumberConfig(min=50.0, max=180.0, unit="bpm"))
    p_bp = Parameter(name="systolic_bp", type="number", number=NumberConfig(min=80.0, max=200.0, unit="mmHg"))

    profile = MachineProfile(name="Medical Monitor", domain="Healthcare", parameters=[p_hr, p_bp])
    gen = SyntheticDataGenerator(seed=555)
    df_raw = gen.generate(profile, num_records=1000, seed=555)

    engine = DomainTemplateEngine()
    df_domain = engine.apply_domain_rules(df_raw, profile, domain="Healthcare")

    corr_domain = df_domain["heart_rate"].corr(df_domain["systolic_bp"])
    assert corr_domain > 0.3, f"Expected positive vital correlation in Healthcare domain, got {corr_domain:.3f}"


def test_ecommerce_domain_cart_total_correlation():
    p_cart = Parameter(name="cart_items", type="number", number=NumberConfig(min=1.0, max=20.0, unit="items"))
    p_tot = Parameter(name="total_amount", type="number", number=NumberConfig(min=5.0, max=500.0, unit="USD"))

    profile = MachineProfile(name="Online Store", domain="E-commerce", parameters=[p_cart, p_tot])
    gen = SyntheticDataGenerator(seed=777)
    df_raw = gen.generate(profile, num_records=1000, seed=777)

    engine = DomainTemplateEngine()
    df_domain = engine.apply_domain_rules(df_raw, profile, domain="E-commerce")

    corr_domain = df_domain["cart_items"].corr(df_domain["total_amount"])
    assert corr_domain > 0.4, f"Expected strong positive cart-amount correlation, got {corr_domain:.3f}"
