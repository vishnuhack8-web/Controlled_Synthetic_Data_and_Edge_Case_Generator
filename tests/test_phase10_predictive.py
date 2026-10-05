import os
import json
import pytest
import pandas as pd

from backend.models import (
    MachineProfile,
    Parameter,
    NumberConfig,
    CategoryConfig
)
from ml.generator import SyntheticDataGenerator
from ml.edge_cases import EdgeCaseEngine
from ml.predictive import PredictiveAnalyticsEngine, REPORT_PATH


def test_predictive_analytics_engine_with_vs_without_edge_cases():
    p1 = Parameter(name="temp", type="number", number=NumberConfig(min=10.0, max=90.0))
    p2 = Parameter(name="pressure", type="number", number=NumberConfig(min=1.0, max=10.0))
    p3 = Parameter(name="status", type="category", category=CategoryConfig(values=["running", "error"]))

    profile = MachineProfile(name="Predictive Machine", parameters=[p1, p2, p3])
    gen = SyntheticDataGenerator(seed=42)
    df_raw = gen.generate(profile, num_records=1000, seed=42)

    engine_edge = EdgeCaseEngine()
    df_with_edges = engine_edge.inject_edge_cases(df_raw, profile, scenario="Combined equipment failure", frequency=10.0, seed=42)

    pred_engine = PredictiveAnalyticsEngine()
    report = pred_engine.train_and_evaluate(df_with_edges)

    # Check metrics existence & bounds
    assert report.model_name == "RandomForest Failure Predictor"
    assert report.with_edge_cases.f1_score > 0.70
    assert report.with_edge_cases.recall > 0.70
    assert report.edge_case_value_gain_f1 > 0.0
    assert report.edge_case_value_gain_recall > 0.0

    # Verify model validation report file saved
    assert os.path.exists(REPORT_PATH)
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        saved_data = json.load(f)
    assert saved_data["model_name"] == "RandomForest Failure Predictor"
    assert "with_edge_cases" in saved_data
    assert "without_edge_cases" in saved_data
