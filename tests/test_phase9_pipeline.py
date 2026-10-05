import pytest
import pandas as pd
import numpy as np

from backend.models import (
    MachineProfile,
    Parameter,
    NumberConfig,
    CategoryConfig,
    DatetimeConfig
)
from ml.generator import SyntheticDataGenerator
from ml.pipeline import DataProcessingPipeline


def test_data_processing_pipeline_features_and_trends():
    p1 = Parameter(name="temperature", type="number", number=NumberConfig(min=10.0, max=90.0))
    p2 = Parameter(name="pressure", type="number", number=NumberConfig(min=1.0, max=10.0))
    p3 = Parameter(name="status", type="category", category=CategoryConfig(values=["ok", "error"]))
    p4 = Parameter(name="timestamp", type="datetime", datetime=DatetimeConfig(interval="every 5 seconds"))

    profile = MachineProfile(name="Pipeline Test Machine", parameters=[p1, p2, p3, p4])
    gen = SyntheticDataGenerator(seed=42)
    df_raw = gen.generate(profile, num_records=200, seed=42)

    # Inject a couple nulls artificially to test imputation
    df_raw.loc[10, "temperature"] = np.nan
    df_raw.loc[15, "status"] = np.nan

    pipeline = DataProcessingPipeline()
    df_processed, trends = pipeline.process(df_raw, profile)

    # 1. Cleaning & Imputation test
    assert df_processed["temperature"].isnull().sum() == 0
    assert df_processed["status"].isnull().sum() == 0

    # 2. Feature engineering columns test
    assert "temperature_lag_1" in df_processed.columns
    assert "temperature_delta" in df_processed.columns
    assert "temperature_rolling_mean_5" in df_processed.columns
    assert "temperature_rolling_std_5" in df_processed.columns
    assert "timestamp_hour" in df_processed.columns
    assert "interaction_temperature_x_pressure" in df_processed.columns

    # 3. Historical trend analytics test
    assert "temperature" in trends
    assert "mean" in trends["temperature"]
    assert "std" in trends["temperature"]
    assert "ema_latest" in trends["temperature"]
    assert "trend_slope" in trends["temperature"]
    assert "trend_direction" in trends["temperature"]
