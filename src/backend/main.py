import os
import webbrowser
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from backend.models import MachineProfile, GenerationConfig, get_config_spec
from backend.llm.ollama_client import OllamaClient
from backend.database import (
    save_machine_profile,
    get_machine_profile_by_id,
    list_machine_profiles,
    list_runs_records,
    get_run_record_by_id,
    init_db
)
from backend.services import GenerationService, RUNS_DIR
from ml.validation import DataQualityValidator
from ml.privacy import PrivacyEvaluator

load_dotenv()
init_db()

app = FastAPI(
    title="AI Synthetic Data & Edge-Case Generation Platform API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_client = OllamaClient()
generation_service = GenerationService()
quality_validator = DataQualityValidator()
privacy_evaluator = PrivacyEvaluator()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ParseMachineRequest(BaseModel):
    description: str = Field(..., description="Paragraph description of the machine/system")


class WhatIfRequest(BaseModel):
    run_id: str
    num_records: Optional[int] = None
    edge_case_frequency: Optional[float] = None
    scenario: Optional[str] = None
    seed: Optional[int] = None
    output_format: Optional[str] = None


@app.on_event("startup")
def open_browser_on_startup():
    try:
        webbrowser.open("http://localhost:8000")
    except Exception:
        pass


@app.get("/", response_class=HTMLResponse)
def root_dashboard():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>SynthEdge API Running</h1>")


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "synthetic-data-platform-backend",
        "version": "1.0.0"
    }


@app.get("/api/config-spec")
def config_spec():
    return get_config_spec()


@app.get("/api/llm-status")
def get_llm_status():
    return llm_client.get_status()


@app.post("/api/parse-machine")
def parse_machine(req: ParseMachineRequest):
    try:
        result = llm_client.parse_machine(req.description)
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error parsing machine description: {str(err)}"
        )


@app.post("/api/machines", response_model=MachineProfile, status_code=status.HTTP_201_CREATED)
def create_machine(profile: MachineProfile):
    try:
        saved = save_machine_profile(profile)
        return saved
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error saving machine profile: {str(err)}"
        )


@app.get("/api/machines", response_model=List[Dict[str, Any]])
def get_all_machines():
    return list_machine_profiles()


@app.get("/api/machines/{machine_id}", response_model=MachineProfile)
def get_machine(machine_id: str):
    profile = get_machine_profile_by_id(machine_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Machine profile with id '{machine_id}' not found"
        )
    return profile


@app.post("/api/generate", status_code=status.HTTP_201_CREATED)
def generate_dataset(config: GenerationConfig):
    try:
        result = generation_service.run_generation_pipeline(config)
        return result
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing generation pipeline: {str(err)}"
        )


@app.get("/api/runs", response_model=List[Dict[str, Any]])
def get_all_runs():
    return list_runs_records()


@app.get("/api/runs/{run_id}")
def get_run(run_id: str):
    run_record = get_run_record_by_id(run_id)
    if not run_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation run with id '{run_id}' not found"
        )
    return run_record


@app.post("/api/validate")
def validate_machine_profile(profile: MachineProfile):
    try:
        df_sample = generation_service.generator.generate(profile, num_records=200, seed=42)
        q_report = quality_validator.validate(df_sample, profile)
        p_report = privacy_evaluator.evaluate(df_sample)
        return {
            "quality_report": q_report.model_dump(),
            "privacy_report": p_report.model_dump(),
            "valid": q_report.passed and p_report.passed
        }
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed: {str(err)}"
        )


@app.get("/api/download/{run_id}")
def download_run_file(run_id: str):
    run_record = get_run_record_by_id(run_id)
    if not run_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run '{run_id}' not found"
        )

    file_path = run_record.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File for run '{run_id}' is missing from storage"
        )

    fmt = run_record.get("output_format", "csv").lower()
    media_types = {
        "csv": "text/csv",
        "json": "application/json",
        "parquet": "application/octet-stream"
    }

    return FileResponse(
        path=file_path,
        media_type=media_types.get(fmt, "text/csv"),
        filename=os.path.basename(file_path)
    )


@app.post("/api/whatif")
def scenario_what_if(req: WhatIfRequest):
    orig_run = get_run_record_by_id(req.run_id)
    if not orig_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Base run '{req.run_id}' not found"
        )

    machine_id = orig_run["machine_id"]
    new_config = GenerationConfig(
        machine_id=machine_id,
        num_records=req.num_records if req.num_records is not None else orig_run["num_records"],
        edge_case_frequency=req.edge_case_frequency if req.edge_case_frequency is not None else orig_run["edge_case_frequency"],
        scenario=req.scenario if req.scenario is not None else orig_run["scenario"],
        seed=req.seed if req.seed is not None else orig_run.get("seed", 42),
        output_format=req.output_format if req.output_format is not None else orig_run["output_format"]
    )

    try:
        new_run = generation_service.run_generation_pipeline(new_config)
        return new_run
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running what-if scenario: {str(err)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=[os.path.dirname(os.path.abspath(__file__))])
