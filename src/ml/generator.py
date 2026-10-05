import re
import time
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from faker import Faker

from backend.models import MachineProfile, Parameter

fake = Faker()


def parse_interval(interval_str: str) -> timedelta:
    if not interval_str:
        return timedelta(seconds=5)
    text = str(interval_str).lower().strip()
    match = re.search(r"(\d+(\.\d+)?)", text)
    num = float(match.group(1)) if match else 5.0

    if "sec" in text or "s" in text:
        return timedelta(seconds=num)
    elif "min" in text or "m" in text:
        return timedelta(minutes=num)
    elif "hour" in text or "h" in text:
        return timedelta(hours=num)
    elif "day" in text or "d" in text:
        return timedelta(days=num)
    elif "ms" in text or "milli" in text:
        return timedelta(milliseconds=num)
    else:
        return timedelta(seconds=num)


class SyntheticDataGenerator:
    """
    Schema-agnostic, vectorized, reproducible synthetic data generator.
    Supports high-performance chunked generation for large scale (up to 1,000,000 records).
    """

    def __init__(self, seed: Optional[int] = 42):
        self.seed = seed
        self._set_seed(seed)

    def _set_seed(self, seed: Optional[int]):
        if seed is not None:
            np.random.seed(seed)
            Faker.seed(seed)

    def generate(self, profile: MachineProfile, num_records: int = 10000, seed: Optional[int] = None) -> pd.DataFrame:
        """
        Generate a synthetic dataset of num_records based on profile schema.
        Uses chunking for num_records > 50,000 for memory efficiency.
        """
        if seed is not None:
            self._set_seed(seed)
        elif self.seed is not None:
            self._set_seed(self.seed)

        chunk_size = 50000
        if num_records <= chunk_size:
            return self._generate_chunk(profile, num_records, offset_index=0)
        else:
            chunks = []
            records_generated = 0
            while records_generated < num_records:
                current_chunk_len = min(chunk_size, num_records - records_generated)
                chunk_df = self._generate_chunk(profile, current_chunk_len, offset_index=records_generated)
                chunks.append(chunk_df)
                records_generated += current_chunk_len
            return pd.concat(chunks, ignore_index=True)

    def _generate_chunk(self, profile: MachineProfile, num_records: int, offset_index: int = 0) -> pd.DataFrame:
        data: Dict[str, Any] = {}

        for param in profile.parameters:
            col_name = param.name

            if param.type == "number" and param.number:
                min_val = param.number.min
                max_val = param.number.max
                dist = param.number.distribution

                if dist == "normal":
                    loc = (min_val + max_val) / 2.0
                    scale = (max_val - min_val) / 6.0
                    if scale <= 0:
                        scale = 1.0
                    vals = np.random.normal(loc=loc, scale=scale, size=num_records)
                    vals = np.clip(vals, min_val, max_val)
                elif dist == "exponential":
                    scale = (max_val - min_val) / 3.0
                    vals = min_val + np.random.exponential(scale=scale, size=num_records)
                    vals = np.clip(vals, min_val, max_val)
                else:  # uniform
                    vals = np.random.uniform(low=min_val, high=max_val, size=num_records)

                data[col_name] = np.round(vals, 3)

            elif param.type == "category" and param.category:
                vals_list = param.category.values
                weights = param.category.weights

                if weights and len(weights) == len(vals_list):
                    probs = np.array(weights, dtype=float)
                    probs = probs / probs.sum()
                else:
                    probs = None

                chosen = np.random.choice(vals_list, size=num_records, p=probs)
                data[col_name] = chosen

            elif param.type == "boolean" and param.boolean:
                true_share = param.boolean.true_share / 100.0
                p_false = 1.0 - true_share
                chosen = np.random.choice([False, True], size=num_records, p=[p_false, true_share])
                data[col_name] = chosen

            elif param.type == "text" and param.text:
                prefix = col_name[:3].upper()
                # Fast vectorized token generation for scale
                tokens = [f"{prefix}-{i + offset_index:06d}" for i in range(num_records)]
                data[col_name] = tokens

            elif param.type == "datetime" and param.datetime:
                start_str = param.datetime.start_time
                try:
                    start_dt = datetime.fromisoformat(start_str)
                except Exception:
                    start_dt = datetime(2026, 1, 1, 0, 0, 0)

                delta = parse_interval(param.datetime.interval)
                base_start = start_dt + offset_index * delta
                timestamps = [base_start + i * delta for i in range(num_records)]
                data[col_name] = [ts.strftime("%Y-%m-%d %H:%M:%S") for ts in timestamps]

            else:
                data[col_name] = np.random.uniform(0, 100, size=num_records)

        return pd.DataFrame(data)
