import pytest
import pandas as pd
import numpy as np

from backend.models import (
    MachineProfile,
    Parameter,
    NumberConfig,
    CategoryConfig
)
from ml.generator import SyntheticDataGenerator
from ml.validation import DataQualityValidator


def test_data_quality_validator_clean_dataset():
    p1 = Parameter(name="temp", type="number", number=NumberConfig(min=10.0, max=90.0, distribution="normal"))
    p2 = Parameter(name="status", type="category", category=CategoryConfig(values=["active", "idle"]))
    profile = MachineProfile(name="Quality Machine", parameters=[p1, p2])

    gen = SyntheticDataGenerator(seed=42)
    df = gen.generate(profile, num_records=1000)

    validator = DataQualityValidator()
    report = validator.validate(df, profile)

    assert report.quality_score >= 85.0
    assert report.schema_compliance_pct == 100.0
    assert report.completeness_pct == 100.0
    assert report.range_satisfaction_pct == 100.0
    assert report.passed is True


def test_data_quality_validator_detects_nulls_and_range_violations():
    p1 = Parameter(name="temp", type="number", number=NumberConfig(min=10.0, max=90.0))
    p2 = Parameter(name="status", type="category", category=CategoryConfig(values=["active", "idle"]))
    profile = MachineProfile(name="Quality Machine", parameters=[p1, p2])

    validator = DataQualityValidator()

    # Create dataset with nulls and out-of-range values
    df_dirty = pd.DataFrame({
        "temp": [15.0, 50.0, 150.0, np.nan, -20.0],  # 150.0 & -20.0 out of range
        "status": ["active", "idle", "INVALID_CAT", "active", "idle"]
    })

    report = validator.validate(df_dirty, profile)
    assert report.completeness_pct < 100.0
    assert report.range_satisfaction_pct < 100.0
    assert report.quality_score < 85.0
