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


def test_generator_all_5_parameter_types_and_ranges():
    p_num = Parameter(name="temp", type="number", number=NumberConfig(min=10.0, max=90.0, unit="°C", distribution="uniform"))
    p_cat = Parameter(name="status", type="category", category=CategoryConfig(values=["ok", "warning", "alarm"]))
    p_bool = Parameter(name="active", type="boolean", boolean=BooleanConfig(true_share=70.0))
    p_txt = Parameter(name="session_token", type="text", text=TextConfig())
    p_dt = Parameter(name="timestamp", type="datetime", datetime=DatetimeConfig(interval="every 10 seconds"))

    profile = MachineProfile(name="Full Test Machine", parameters=[p_num, p_cat, p_bool, p_txt, p_dt])
    generator = SyntheticDataGenerator(seed=123)

    df = generator.generate(profile, num_records=1000)
    assert len(df) == 1000
    assert list(df.columns) == ["temp", "status", "active", "session_token", "timestamp"]

    # Check number range
    assert (df["temp"] >= 10.0).all()
    assert (df["temp"] <= 90.0).all()

    # Check category values
    assert set(df["status"].unique()).issubset({"ok", "warning", "alarm"})

    # Check boolean values
    assert set(df["active"].unique()).issubset({True, False})

    # Check text non-empty tokens
    assert df["session_token"].str.len().gt(0).all()

    # Check datetime format
    assert pd.to_datetime(df["timestamp"]).notnull().all()


def test_seed_reproducibility():
    p1 = Parameter(name="sensor_val", type="number", number=NumberConfig(min=0.0, max=100.0))
    p2 = Parameter(name="state", type="category", category=CategoryConfig(values=["A", "B", "C"]))
    profile = MachineProfile(name="Seeded Machine", parameters=[p1, p2])

    gen1 = SyntheticDataGenerator()
    df1 = gen1.generate(profile, num_records=500, seed=42)

    gen2 = SyntheticDataGenerator()
    df2 = gen2.generate(profile, num_records=500, seed=42)

    pd.testing.assert_frame_equal(df1, df2)


def test_different_seeds_produce_different_outputs():
    p1 = Parameter(name="sensor_val", type="number", number=NumberConfig(min=0.0, max=100.0))
    profile = MachineProfile(name="Seeded Machine", parameters=[p1])

    gen1 = SyntheticDataGenerator()
    df1 = gen1.generate(profile, num_records=500, seed=100)

    gen2 = SyntheticDataGenerator()
    df2 = gen2.generate(profile, num_records=500, seed=200)

    assert not df1.equals(df2)


def test_distributions_uniform_normal_exponential():
    p_unif = Parameter(name="unif", type="number", number=NumberConfig(min=0.0, max=100.0, distribution="uniform"))
    p_norm = Parameter(name="norm", type="number", number=NumberConfig(min=0.0, max=100.0, distribution="normal"))
    p_exp = Parameter(name="exp", type="number", number=NumberConfig(min=0.0, max=100.0, distribution="exponential"))

    profile = MachineProfile(name="Distributions Machine", parameters=[p_unif, p_norm, p_exp])
    gen = SyntheticDataGenerator(seed=999)
    df = gen.generate(profile, num_records=5000)

    # All bounded by min and max
    assert (df["unif"] >= 0.0).all() and (df["unif"] <= 100.0).all()
    assert (df["norm"] >= 0.0).all() and (df["norm"] <= 100.0).all()
    assert (df["exp"] >= 0.0).all() and (df["exp"] <= 100.0).all()

    # Normal distribution mean should be centered near 50
    assert 45.0 <= df["norm"].mean() <= 55.0

    # Exponential distribution should be right-skewed (median < mean)
    assert df["exp"].median() < df["exp"].mean()
