import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from backend.models import MachineProfile


class DataProcessingPipeline:
    """
    Data processing pipeline for synthetic datasets.
    Provides:
    1. Cleaning & Imputation (median for numeric, mode for categorical).
    2. Feature Engineering (lag features, rolling mean/std, delta change, interaction terms, datetime breakdown).
    3. Historical Trend Analysis (EMA trends, cumulative drift, summary statistics).
    """

    def process(self, df: pd.DataFrame, profile: MachineProfile) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Process raw DataFrame: clean missing data, generate engineered features, compute trend analytics.
        Returns (featured_df, trend_analytics_dict).
        """
        processed_df = df.copy()
        if len(processed_df) == 0:
            return processed_df, {}

        # 1. Cleaning & Imputation
        num_cols = [p.name for p in profile.parameters if p.type == "number" and p.name in processed_df.columns]
        cat_cols = [p.name for p in profile.parameters if p.type == "category" and p.name in processed_df.columns]
        dt_cols = [p.name for p in profile.parameters if p.type == "datetime" and p.name in processed_df.columns]

        for col in num_cols:
            if processed_df[col].isnull().any():
                med = processed_df[col].median()
                processed_df[col] = processed_df[col].fillna(med if not pd.isna(med) else 0.0)

        for col in cat_cols:
            if processed_df[col].isnull().any():
                mode_val = processed_df[col].mode()
                fill_val = mode_val.iloc[0] if len(mode_val) > 0 else "UNKNOWN"
                processed_df[col] = processed_df[col].fillna(fill_val)

        # 2. Feature Engineering
        # a. Datetime features
        for dt_col in dt_cols:
            try:
                ts_series = pd.to_datetime(processed_df[dt_col], errors="coerce")
                processed_df[f"{dt_col}_hour"] = ts_series.dt.hour.fillna(0).astype(int)
                processed_df[f"{dt_col}_dayofweek"] = ts_series.dt.dayofweek.fillna(0).astype(int)
            except Exception:
                pass

        # b. Lag, Rolling, and Delta features for numeric columns
        for col in num_cols:
            series = pd.to_numeric(processed_df[col], errors="coerce").fillna(0.0)
            
            # Lag 1
            processed_df[f"{col}_lag_1"] = series.shift(1).bfill()
            # Delta change
            processed_df[f"{col}_delta"] = (series - processed_df[f"{col}_lag_1"]).round(3)
            # Rolling 5-step mean and std
            processed_df[f"{col}_rolling_mean_5"] = series.rolling(window=5, min_periods=1).mean().round(3)
            processed_df[f"{col}_rolling_std_5"] = series.rolling(window=5, min_periods=1).std().fillna(0.0).round(3)

        # c. Interaction terms for pairs of numeric columns
        if len(num_cols) >= 2:
            c1, c2 = num_cols[0], num_cols[1]
            s1 = pd.to_numeric(processed_df[c1], errors="coerce").fillna(1.0)
            s2 = pd.to_numeric(processed_df[c2], errors="coerce").fillna(1.0)
            processed_df[f"interaction_{c1}_x_{c2}"] = (s1 * s2).round(3)

        # 3. Historical Trend Analysis
        trend_analytics = {}
        for col in num_cols:
            series = pd.to_numeric(processed_df[col], errors="coerce").dropna()
            if len(series) > 0:
                ema_5 = series.ewm(span=5, adjust=False).mean()
                cumsum = series.cumsum()
                slope = float(np.polyfit(np.arange(len(series)), series.values, 1)[0]) if len(series) > 1 else 0.0

                trend_analytics[col] = {
                    "mean": float(np.round(series.mean(), 3)),
                    "std": float(np.round(series.std(), 3)),
                    "min": float(np.round(series.min(), 3)),
                    "max": float(np.round(series.max(), 3)),
                    "median": float(np.round(series.median(), 3)),
                    "ema_latest": float(np.round(ema_5.iloc[-1], 3)),
                    "cumsum_total": float(np.round(cumsum.iloc[-1], 3)),
                    "trend_slope": float(np.round(slope, 5)),
                    "trend_direction": "increasing" if slope > 0.01 else ("decreasing" if slope < -0.01 else "stable")
                }

        return processed_df, trend_analytics
