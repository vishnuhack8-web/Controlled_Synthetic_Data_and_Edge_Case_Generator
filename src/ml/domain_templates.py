import numpy as np
import pandas as pd
from typing import Optional
from backend.models import MachineProfile


class DomainTemplateEngine:
    """
    Domain templates rules engine.
    Layers domain-specific statistical correlations and business rules on top of user-defined parameters.
    Supports 5 domains:
    1. IoT / Manufacturing (thermal-speed-vibration physics correlations)
    2. Logistics (distance-speed-fuel & package weight correlations)
    3. Finance (transaction amount & fraud/risk score correlations)
    4. Healthcare (heart rate, blood pressure & vital alert correlations)
    5. E-commerce (cart size, checkout duration & payment type correlations)
    """

    SUPPORTED_DOMAINS = [
        "IoT / Manufacturing",
        "Logistics",
        "Finance",
        "Healthcare",
        "E-commerce"
    ]

    def apply_domain_rules(self, df: pd.DataFrame, profile: MachineProfile, domain: str) -> pd.DataFrame:
        """
        Apply realistic physics and business correlations for the given domain.
        Re-clips numeric values to parameter min/max bounds.
        """
        df = df.copy()
        num_records = len(df)
        if num_records == 0:
            return df

        num_params_map = {p.name: p.number for p in profile.parameters if p.type == "number" and p.number}
        cols_lower = {c.lower(): c for c in df.columns}

        if domain == "IoT / Manufacturing":
            # Rule 1: High speed/power draw correlates with temperature rise
            speed_col = cols_lower.get("motor_speed") or cols_lower.get("speed") or cols_lower.get("rpm") or cols_lower.get("power_draw")
            temp_col = cols_lower.get("temperature") or cols_lower.get("temp") or cols_lower.get("internal_temp")

            if speed_col and temp_col and speed_col in df.columns and temp_col in df.columns:
                speed_norm = (df[speed_col] - df[speed_col].min()) / (df[speed_col].max() - df[speed_col].min() + 1e-6)
                temp_cfg = num_params_map.get(temp_col)
                if temp_cfg:
                    temp_range = temp_cfg.max - temp_cfg.min
                    thermal_effect = speed_norm * (temp_range * 0.4) + np.random.normal(0, temp_range * 0.05, size=num_records)
                    df[temp_col] = np.clip(df[temp_col] + thermal_effect, temp_cfg.min, temp_cfg.max).round(3)

            # Rule 2: High vibration correlates with status == "warning" / "error"
            vib_col = cols_lower.get("vibration")
            status_col = cols_lower.get("operating_mode") or cols_lower.get("status") or cols_lower.get("machine_status")

            if vib_col and status_col and vib_col in df.columns and status_col in df.columns:
                vib_norm = (df[vib_col] - df[vib_col].min()) / (df[vib_col].max() - df[vib_col].min() + 1e-6)
                high_vib_idx = df[vib_norm > 0.75].index
                unique_cats = list(df[status_col].unique())
                err_cats = [c for c in unique_cats if "err" in str(c).lower() or "warn" in str(c).lower()]
                if err_cats and len(high_vib_idx) > 0:
                    df.loc[high_vib_idx, status_col] = np.random.choice(err_cats, size=len(high_vib_idx))

        elif domain == "Logistics":
            # Rule 1: High package weight / volume correlates with lower speed
            weight_col = cols_lower.get("weight") or cols_lower.get("fill_level") or cols_lower.get("cargo_weight")
            speed_col = cols_lower.get("speed") or cols_lower.get("delivery_speed") or cols_lower.get("vehicle_speed")

            if weight_col and speed_col and weight_col in df.columns and speed_col in df.columns:
                weight_norm = (df[weight_col] - df[weight_col].min()) / (df[weight_col].max() - df[weight_col].min() + 1e-6)
                speed_cfg = num_params_map.get(speed_col)
                if speed_cfg:
                    drag_effect = -1.0 * weight_norm * ((speed_cfg.max - speed_cfg.min) * 0.4)
                    df[speed_col] = np.clip(df[speed_col] + drag_effect, speed_cfg.min, speed_cfg.max).round(3)

        elif domain == "Finance":
            # Rule 1: High transaction withdrawal amount correlates with higher risk flag or fee
            amount_col = cols_lower.get("transaction_amount") or cols_lower.get("withdrawal_amount") or cols_lower.get("amount")
            risk_col = cols_lower.get("risk_score") or cols_lower.get("fraud_flag") or cols_lower.get("is_flagged")

            if amount_col and amount_col in df.columns:
                amount_norm = (df[amount_col] - df[amount_col].min()) / (df[amount_col].max() - df[amount_col].min() + 1e-6)
                if risk_col and risk_col in df.columns:
                    high_amt_idx = df[amount_norm > 0.85].index
                    if len(high_amt_idx) > 0:
                        df.loc[high_amt_idx, risk_col] = True

        elif domain == "Healthcare":
            # Rule 1: High heart rate correlates with elevated blood pressure
            hr_col = cols_lower.get("heart_rate") or cols_lower.get("pulse")
            bp_col = cols_lower.get("blood_pressure") or cols_lower.get("systolic_bp")

            if hr_col and bp_col and hr_col in df.columns and bp_col in df.columns:
                hr_norm = (df[hr_col] - df[hr_col].min()) / (df[hr_col].max() - df[hr_col].min() + 1e-6)
                bp_cfg = num_params_map.get(bp_col)
                if bp_cfg:
                    bp_effect = hr_norm * ((bp_cfg.max - bp_cfg.min) * 0.50)
                    df[bp_col] = np.clip(df[bp_col] + bp_effect, bp_cfg.min, bp_cfg.max).round(3)

        elif domain == "E-commerce":
            # Rule 1: High item count correlates with higher order total amount / checkout duration
            item_col = cols_lower.get("item_count") or cols_lower.get("cart_items") or cols_lower.get("inventory_stock")
            total_col = cols_lower.get("total_amount") or cols_lower.get("checkout_duration") or cols_lower.get("transaction_amount")

            if item_col and total_col and item_col in df.columns and total_col in df.columns:
                item_norm = (df[item_col] - df[item_col].min()) / (df[item_col].max() - df[item_col].min() + 1e-6)
                tot_cfg = num_params_map.get(total_col)
                if tot_cfg:
                    tot_effect = item_norm * ((tot_cfg.max - tot_cfg.min) * 0.5)
                    df[total_col] = np.clip(df[total_col] + tot_effect, tot_cfg.min, tot_cfg.max).round(3)

        return df
