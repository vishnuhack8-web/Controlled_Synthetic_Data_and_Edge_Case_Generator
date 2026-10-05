import os
import json
import sqlite3
from typing import List, Optional, Dict, Any
from backend.models import MachineProfile

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "app.db")


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS machines (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            suggested_domain TEXT,
            domain TEXT,
            parameters_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            machine_id TEXT NOT NULL,
            machine_name TEXT NOT NULL,
            num_records INTEGER NOT NULL,
            edge_case_frequency REAL NOT NULL,
            scenario TEXT NOT NULL,
            seed INTEGER,
            output_format TEXT NOT NULL,
            quality_score REAL,
            privacy_score REAL,
            file_path TEXT NOT NULL,
            run_metadata_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (machine_id) REFERENCES machines(id)
        );
    """)
    conn.commit()
    conn.close()


def save_machine_profile(profile: MachineProfile) -> MachineProfile:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    params_json = json.dumps([p.model_dump() for p in profile.parameters])

    cursor.execute("""
        INSERT OR REPLACE INTO machines (id, name, description, suggested_domain, domain, parameters_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (profile.id, profile.name, profile.description, profile.suggested_domain, profile.domain, params_json))

    conn.commit()
    conn.close()
    return profile


def get_machine_profile_by_id(machine_id: str) -> Optional[MachineProfile]:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM machines WHERE id = ?", (machine_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    raw_params = json.loads(row["parameters_json"])
    return MachineProfile(
        id=row["id"],
        name=row["name"],
        description=row["description"] or "",
        suggested_domain=row["suggested_domain"] or "IoT / Manufacturing",
        domain=row["domain"] or "IoT / Manufacturing",
        parameters=raw_params
    )


def list_machine_profiles() -> List[Dict[str, Any]]:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, description, suggested_domain, domain, parameters_json, created_at FROM machines ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        params = json.loads(row["parameters_json"])
        results.append({
            "id": row["id"],
            "name": row["name"],
            "description": row["description"] or "",
            "suggested_domain": row["suggested_domain"] or "IoT / Manufacturing",
            "domain": row["domain"] or "IoT / Manufacturing",
            "parameter_count": len(params),
            "created_at": row["created_at"]
        })
    return results


def save_run_record(
    run_id: str,
    machine_id: str,
    machine_name: str,
    num_records: int,
    edge_case_frequency: float,
    scenario: str,
    seed: Optional[int],
    output_format: str,
    quality_score: float,
    privacy_score: float,
    file_path: str,
    metadata_dict: Dict[str, Any]
):
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO runs (
            run_id, machine_id, machine_name, num_records, edge_case_frequency,
            scenario, seed, output_format, quality_score, privacy_score, file_path, run_metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id, machine_id, machine_name, num_records, edge_case_frequency,
        scenario, seed, output_format, quality_score, privacy_score, file_path,
        json.dumps(metadata_dict)
    ))

    conn.commit()
    conn.close()


def get_run_record_by_id(run_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    meta = json.loads(row["run_metadata_json"])
    meta["run_id"] = row["run_id"]
    meta["file_path"] = row["file_path"]
    meta["created_at"] = row["created_at"]
    return meta


def list_runs_records() -> List[Dict[str, Any]]:
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT run_id, machine_id, machine_name, num_records, edge_case_frequency, scenario,
               output_format, quality_score, privacy_score, created_at
        FROM runs ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]
