import numpy as np
import pandas as pd
from typing import Optional, List
from backend.models import MachineProfile, Parameter


class EdgeCaseEngine:
    """
    Schema-agnostic edge-case and anomaly generation engine.
    Injects realistic failure scenarios into datasets based on field TYPES and user ranges.
    Guarantees exact edge-case row count equal to round(num_records * (frequency / 100)).
    """

    SCENARIOS = [
        "Boundary values",
        "Missing or corrupted data",
        "Combined equipment failure",
        "Network outage"
    ]

    def inject_edge_cases(
        self,
        df: pd.DataFrame,
        profile: MachineProfile,
        scenario: str = "Combined equipment failure",
        frequency: float = 5.0,
        seed: Optional[int] = 42
    ) -> pd.DataFrame:
        """
        Inject edge-case scenarios into the DataFrame.
        Adds metadata columns: 'is_edge_case' (0/1) and 'edge_case_type'.
        """
        df = df.copy()
        num_records = len(df)
        target_count = int(round(num_records * (frequency / 100.0)))
        target_count = max(0, min(num_records, target_count))

        # Add tracking metadata columns
        df["is_edge_case"] = 0
        df["edge_case_type"] = "Normal"

        if target_count == 0:
            return df

        if seed is not None:
            np.random.seed(seed)

        # Pick random row indices to convert into edge cases
        edge_indices = np.random.choice(df.index, size=target_count, replace=False)
        df.loc[edge_indices, "is_edge_case"] = 1
        df.loc[edge_indices, "edge_case_type"] = scenario

        num_params = [p for p in profile.parameters if p.type == "number" and p.number]
        cat_params = [p for p in profile.parameters if p.type == "category" and p.category]
        bool_params = [p for p in profile.parameters if p.type == "boolean" and p.boolean]
        text_params = [p for p in profile.parameters if p.type == "text"]
        dt_params = [p for p in profile.parameters if p.type == "datetime"]

        if scenario == "Boundary values":
            # For numbers: exact min, max, slightly lower than min, slightly higher than max
            for idx in edge_indices:
                for p in num_params:
                    min_val = p.number.min
                    max_val = p.number.max
                    choice = np.random.choice(["exact_min", "exact_max", "below_min", "above_max"])
                    if choice == "exact_min":
                        val = min_val
                    elif choice == "exact_max":
                        val = max_val
                    elif choice == "below_min":
                        val = min_val - abs(min_val * 0.15 + 1.0)
                    else:
                        val = max_val + abs(max_val * 0.15 + 1.0)
                    df.loc[idx, p.name] = round(float(val), 3)

                for p in cat_params:
                    # Rare or unseen boundary category
                    rarest_cat = p.category.values[-1] if len(p.category.values) > 0 else "UNKNOWN_STATE"
                    df.loc[idx, p.name] = f"OUT_OF_BOUNDS_{rarest_cat}"

                for p in bool_params:
                    df.loc[idx, p.name] = not bool(df.loc[idx, p.name])

        elif scenario == "Missing or corrupted data":
            # Cast all profile parameter columns to object dtype to allow mixed nulls/corrupt strings
            for p in profile.parameters:
                df[p.name] = df[p.name].astype(object)

            for idx in edge_indices:
                corrupt_type = np.random.choice(["null", "corrupted_type", "malformed_string"])
                corrupt_params = np.random.choice(profile.parameters, size=max(1, len(profile.parameters) // 2), replace=False)
                for p in corrupt_params:
                    if corrupt_type == "null":
                        df.loc[idx, p.name] = np.nan
                    elif corrupt_type == "corrupted_type":
                        df.loc[idx, p.name] = "ERR_CORRUPT_VALUE_99999"
                    else:
                        df.loc[idx, p.name] = "###MALFORMED_DATA_NULL###"

        elif scenario == "Combined equipment failure":
            for idx in edge_indices:
                if len(num_params) >= 2:
                    p1, p2 = np.random.choice(num_params, size=2, replace=False)
                    df.loc[idx, p1.name] = round(float(p1.number.max * 1.5 + 5.0), 3)  # spike high
                    df.loc[idx, p2.name] = round(float(p2.number.min - 5.0), 3)        # drop low
                elif len(num_params) == 1:
                    p1 = num_params[0]
                    df.loc[idx, p1.name] = round(float(p1.number.max * 2.0 + 10.0), 3)

                for p in cat_params:
                    if any(term in p.name.lower() for term in ["status", "mode", "state", "condition"]):
                        error_vals = [v for v in p.category.values if any(e in v.lower() for e in ["error", "fail", "alarm", "crit", "down"])]
                        if error_vals:
                            df.loc[idx, p.name] = error_vals[0]
                        else:
                            df.loc[idx, p.name] = "FAILURE_CRITICAL"

        elif scenario == "Network outage":
            for idx in edge_indices:
                for p in dt_params:
                    choice = np.random.choice(["time_gap", "duplicate", "out_of_order"])
                    if choice == "time_gap":
                        df.loc[idx, p.name] = "1970-01-01 00:00:00"
                    elif choice == "duplicate":
                        prev_idx = max(0, idx - 1)
                        df.loc[idx, p.name] = df.loc[prev_idx, p.name]

                for p in cat_params:
                    if any(term in p.name.lower() for term in ["network", "connect", "wifi", "link", "online"]):
                        df.loc[idx, p.name] = "offline"

                for p in bool_params:
                    if any(term in p.name.lower() for term in ["connect", "online", "link"]):
                        df.loc[idx, p.name] = False

        return df
