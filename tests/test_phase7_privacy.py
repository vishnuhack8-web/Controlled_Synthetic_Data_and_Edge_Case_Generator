import pytest
import pandas as pd
import numpy as np

from backend.models import (
    MachineProfile,
    Parameter,
    NumberConfig,
    CategoryConfig,
    TextConfig
)
from ml.generator import SyntheticDataGenerator
from ml.privacy import PrivacyEvaluator


def test_privacy_evaluator_clean_synthetic_dataset():
    p_temp = Parameter(name="temperature", type="number", number=NumberConfig(min=0.0, max=100.0))
    p_status = Parameter(name="status", type="category", category=CategoryConfig(values=["ok", "error"]))
    p_token = Parameter(name="token", type="text", text=TextConfig())

    profile = MachineProfile(name="Privacy Test Machine", parameters=[p_temp, p_status, p_token])
    gen = SyntheticDataGenerator(seed=42)
    df = gen.generate(profile, num_records=500)

    evaluator = PrivacyEvaluator()
    report = evaluator.evaluate(df)

    assert report.privacy_score >= 90.0
    assert report.pii_leaks_count == 0
    assert report.passed is True
    assert report.nearest_neighbor_min_dist >= 0.0


def test_privacy_evaluator_pii_detection():
    evaluator = PrivacyEvaluator()

    # Create dataset with artificial real SSNs and emails
    df_dirty = pd.DataFrame({
        "temperature": [25.0, 30.0, 35.0],
        "user_email": ["john.doe@example.com", "jane.smith@test.org", "ID-1234-5678"],
        "user_ssn": ["123-45-6789", "987-65-4321", "ID-9999-0000"]
    })

    report = evaluator.evaluate(df_dirty)
    assert report.pii_leaks_count >= 2
    assert report.passed is False
    assert report.privacy_score < 80.0


def test_exact_matches_against_reference_dataset():
    evaluator = PrivacyEvaluator()

    df_synth = pd.DataFrame({
        "val": [10.0, 20.0, 30.0],
        "category": ["A", "B", "C"]
    })

    df_real = pd.DataFrame({
        "val": [10.0, 20.0, 99.0],
        "category": ["A", "B", "Z"]
    })

    report = evaluator.evaluate(df_synth, reference_df=df_real)
    assert report.exact_matches_found == 2
