import os
import json
import uuid
import pandas as pd
from typing import Dict, Any, Optional

from backend.models import MachineProfile, GenerationConfig
from backend.database import get_machine_profile_by_id, save_run_record, get_run_record_by_id
from ml.generator import SyntheticDataGenerator
from ml.domain_templates import DomainTemplateEngine
from ml.edge_cases import EdgeCaseEngine
from ml.pipeline import DataProcessingPipeline
from ml.privacy import PrivacyEvaluator
from ml.validation import DataQualityValidator
from ml.predictive import PredictiveAnalyticsEngine

RUNS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "runs")


class GenerationService:
    def __init__(self):
        os.makedirs(RUNS_DIR, exist_ok=True)
        self.generator = SyntheticDataGenerator()
        self.domain_engine = DomainTemplateEngine()
        self.edge_engine = EdgeCaseEngine()
        self.pipeline = DataProcessingPipeline()
        self.privacy_evaluator = PrivacyEvaluator()
        self.quality_validator = DataQualityValidator()
        self.predictive_engine = PredictiveAnalyticsEngine()

    def run_generation_pipeline(self, config: GenerationConfig, override_profile: Optional[MachineProfile] = None) -> Dict[str, Any]:
        """
        Execute full end-to-end synthetic data generation pipeline:
        1. Fetch MachineProfile
        2. Vectorized schema-driven generation
        3. Domain rules & correlations application
        4. Edge-case scenario injection
        5. Data processing & feature engineering
        6. Privacy evaluation
        7. Data quality validation
        8. Predictive analytics modeling
        9. Export dataset & persist run metadata
        """
        if override_profile:
            profile = override_profile
        else:
            profile = get_machine_profile_by_id(config.machine_id)
            if not profile:
                raise ValueError(f"Machine profile '{config.machine_id}' not found")

        run_id = str(uuid.uuid4())

        df_raw = self.generator.generate(profile, num_records=config.num_records, seed=config.seed)
        df_domain = self.domain_engine.apply_domain_rules(df_raw, profile, domain=profile.domain)
        df_edge = self.edge_engine.inject_edge_cases(
            df_domain,
            profile,
            scenario=config.scenario,
            frequency=config.edge_case_frequency,
            seed=config.seed
        )

        df_processed, trend_analytics = self.pipeline.process(df_edge, profile)

        # Convert all CSV column header names in first row to UPPERCASE
        df_processed.columns = [str(col).upper() for col in df_processed.columns]

        privacy_report = self.privacy_evaluator.evaluate(df_processed)
        quality_report = self.quality_validator.validate(df_processed, profile)
        predictive_report = self.predictive_engine.train_and_evaluate(df_processed)

        file_ext = config.output_format.lower()
        file_name = f"dataset_{run_id}.{file_ext}"
        file_path = os.path.join(RUNS_DIR, file_name)

        if file_ext == "csv":
            df_processed.to_csv(file_path, index=False)
        elif file_ext == "json":
            df_processed.to_json(file_path, orient="records", indent=2)
        elif file_ext == "parquet":
            df_processed.to_parquet(file_path, index=False)
        else:
            df_processed.to_csv(file_path, index=False)
            file_ext = "csv"

        edge_col = "IS_EDGE_CASE" if "IS_EDGE_CASE" in df_processed.columns else "is_edge_case"
        type_col = "EDGE_CASE_TYPE" if "EDGE_CASE_TYPE" in df_processed.columns else "edge_case_type"

        edge_breakdown = df_processed[type_col].value_counts().to_dict() if type_col in df_processed.columns else {}
        total_edge_cases = int((df_processed[edge_col] == 1).sum()) if edge_col in df_processed.columns else 0

        preview_df = df_processed.head(20).copy()
        preview_rows = preview_df.fillna("").to_dict(orient="records")

        run_payload = {
            "run_id": run_id,
            "machine_id": profile.id,
            "machine_name": profile.name,
            "domain": profile.domain,
            "num_records": config.num_records,
            "edge_case_frequency": config.edge_case_frequency,
            "total_edge_cases": total_edge_cases,
            "scenario": config.scenario,
            "seed": config.seed,
            "output_format": file_ext,
            "file_name": file_name,
            "quality_report": quality_report.model_dump(),
            "privacy_report": privacy_report.model_dump(),
            "predictive_report": predictive_report.model_dump(),
            "trend_analytics": trend_analytics,
            "edge_case_breakdown": edge_breakdown,
            "preview_rows": preview_rows,
            "columns": list(df_processed.columns)
        }

        save_run_record(
            run_id=run_id,
            machine_id=profile.id,
            machine_name=profile.name,
            num_records=config.num_records,
            edge_case_frequency=config.edge_case_frequency,
            scenario=config.scenario,
            seed=config.seed,
            output_format=file_ext,
            quality_score=quality_report.quality_score,
            privacy_score=privacy_report.privacy_score,
            file_path=file_path,
            metadata_dict=run_payload
        )

        return run_payload
