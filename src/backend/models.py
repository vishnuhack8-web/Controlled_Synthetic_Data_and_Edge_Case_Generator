from typing import List, Optional, Literal
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator, field_validator


class NumberConfig(BaseModel):
    min: float = 0.0
    max: float = 100.0
    unit: str = ""
    distribution: Literal["uniform", "normal", "exponential"] = "uniform"

    @model_validator(mode="after")
    def check_min_max(self):
        if self.min >= self.max:
            raise ValueError(f"Number min ({self.min}) must be strictly less than max ({self.max})")
        return self


class CategoryConfig(BaseModel):
    values: List[str] = Field(default_factory=lambda: ["active", "inactive"])
    weights: Optional[List[float]] = None

    @field_validator("values")
    @classmethod
    def check_values_length(cls, v):
        if len(v) < 2:
            raise ValueError("Category parameters must have at least 2 distinct values")
        # Ensure values are non-empty strings
        cleaned = [str(x).strip() for x in v if str(x).strip()]
        if len(cleaned) < 2:
            raise ValueError("Category parameters must have at least 2 non-empty string values")
        return cleaned

    @model_validator(mode="after")
    def check_weights(self):
        if self.weights is not None:
            if len(self.weights) != len(self.values):
                raise ValueError("Category weights length must match values length")
            if any(w < 0 for w in self.weights):
                raise ValueError("Category weights cannot be negative")
            if sum(self.weights) <= 0:
                raise ValueError("Sum of category weights must be greater than zero")
        return self


class TextConfig(BaseModel):
    note: str = "fake tokens only"
    format: str = "alphanumeric"


class BooleanConfig(BaseModel):
    true_share: float = Field(default=50.0, description="Percentage share of True values (0 to 100)")

    @field_validator("true_share")
    @classmethod
    def check_true_share_range(cls, v):
        if v < 0.0 or v > 100.0:
            raise ValueError(f"Boolean true_share must be between 0 and 100 inclusive, got {v}")
        return v


class DatetimeConfig(BaseModel):
    interval: str = "every 5 seconds"
    start_time: str = "2026-01-01T00:00:00"


class Parameter(BaseModel):
    name: str
    type: Literal["number", "category", "text", "boolean", "datetime"]
    number: Optional[NumberConfig] = None
    category: Optional[CategoryConfig] = None
    text: Optional[TextConfig] = None
    boolean: Optional[BooleanConfig] = None
    datetime: Optional[DatetimeConfig] = None

    @model_validator(mode="after")
    def validate_type_configs(self):
        if not self.name or not self.name.strip():
            raise ValueError("Parameter name is required and cannot be empty")
        self.name = self.name.strip()

        if self.type == "number":
            if self.number is None:
                self.number = NumberConfig()
        elif self.type == "category":
            if self.category is None:
                self.category = CategoryConfig()
        elif self.type == "text":
            if self.text is None:
                self.text = TextConfig()
        elif self.type == "boolean":
            if self.boolean is None:
                self.boolean = BooleanConfig()
        elif self.type == "datetime":
            if self.datetime is None:
                self.datetime = DatetimeConfig()
        return self


class MachineProfile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = "Default Machine Profile"
    description: str = ""
    suggested_domain: str = "IoT / Manufacturing"
    domain: str = "IoT / Manufacturing"
    parameters: List[Parameter] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_machine_profile(self):
        if not self.parameters:
            raise ValueError("MachineProfile must have at least one parameter")
        
        seen_names = set()
        for param in self.parameters:
            lower_name = param.name.lower()
            if lower_name in seen_names:
                raise ValueError(f"Duplicate parameter name found (case-insensitive): '{param.name}'")
            seen_names.add(lower_name)
        return self


class GenerationConfig(BaseModel):
    machine_id: str
    num_records: int = Field(default=10000, ge=100, le=100000, description="Number of records to generate (100 to 100,000)")
    edge_case_frequency: float = Field(default=5.0, ge=1.0, le=20.0, description="Target edge-case frequency percentage (1% to 20%)")
    scenario: Literal["Boundary values", "Missing or corrupted data", "Combined equipment failure", "Network outage"] = "Combined equipment failure"
    seed: Optional[int] = 42
    output_format: Literal["csv", "json", "parquet"] = "csv"


def get_config_spec():
    """Export single source of truth configuration schema."""
    return {
        "machine_profile_schema": MachineProfile.model_json_schema(),
        "parameter_schema": Parameter.model_json_schema(),
        "generation_config_schema": GenerationConfig.model_json_schema(),
        "domains": ["IoT / Manufacturing", "Logistics", "Finance", "Healthcare", "E-commerce"],
        "scenarios": [
            "Boundary values",
            "Missing or corrupted data",
            "Combined equipment failure",
            "Network outage"
        ],
        "output_formats": ["csv", "json", "parquet"],
        "defaults": {
            "num_records": 10000,
            "min_records": 100,
            "max_records": 100000,
            "edge_case_frequency": 5.0,
            "min_edge_case_frequency": 1.0,
            "max_edge_case_frequency": 20.0,
            "default_scenario": "Combined equipment failure"
        }
    }
