"""Run a synthetic WriteLab -> paper-governance handoff E2E probe.

This probe creates a synthetic diagnosis report through the real WriteLab
FastAPI routes, downloads the metadata-only handoff ZIP, and validates that ZIP
with the agent-acceptance governance validator. It does not process real paper
content and uses an isolated SQLite database under the evidence directory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any

from validate_writelab_handoff import validate_writelab_handoff


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = ROOT / "_reports" / "writelab-synthetic-e2e-a1"
DEFAULT_WRITELAB_BACKEND = Path("D:/writelab/backend")
FORBIDDEN_MARKERS = [
    "REAL_PAPER_TEXT",
    "USER_PRIVATE_TEXT",
    "RAW_TRANSCRIPT",
    "AUTHOR_IDENTITY",
]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _import_writelab_app(writelab_backend: Path, db_path: Path):
    backend = writelab_backend.resolve()
    if not backend.exists():
        raise RuntimeError(f"WriteLab backend path does not exist: {backend}")

    os.environ["WRITELAB_TEST_DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))

    from fastapi.testclient import TestClient
    from app.core.database import Base, engine
    from app.main import app

    Base.metadata.create_all(bind=engine)
    return TestClient(app), engine


def _synthetic_diagnosis_payload() -> dict[str, Any]:
    return {
        "paragraph": FORBIDDEN_MARKERS[0],
        "diagnosis": {
            "actual_function": "path_design",
            "expected_function": "path_design",
            "function_match_score": 86,
            "main_claim": FORBIDDEN_MARKERS[1],
            "overall_comment": FORBIDDEN_MARKERS[3],
            "problems": [
                {
                    "type": "weak_mechanism",
                    "severity": "medium",
                    "text_span": FORBIDDEN_MARKERS[2],
                    "explanation": "synthetic internal explanation",
                },
                {
                    "type": "template_expression",
                    "severity": "low",
                    "text_span": "synthetic raw span",
                },
            ],
        },
        "expression_report": {
            "sentence_count": 4,
            "avg_sentence_length": 28.5,
            "abstract_noun_density": 0.25,
            "dunhao_density": 0.02,
            "template_sentence_count": 2,
            "normative_expression_count": 3,
            "ai_like_risk": "medium",
            "risks": [
                {
                    "type": "template",
                    "severity": "medium",
                    "text_span": "synthetic risk span",
                }
            ],
        },
    }


def _scan_zip_for_markers(zip_path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        joined = "\n".join(zf.read(name).decode("utf-8", errors="replace") for name in zf.namelist())

    hits = {
        f"marker_{index}": marker in joined
        for index, marker in enumerate(FORBIDDEN_MARKERS, start=1)
    }
    return {
        "zip_path": str(zip_path),
        "pass": not any(hits.values()),
        "marker_count": len(hits),
        "hits_by_label": hits,
    }


def run_probe(writelab_backend: Path, output_dir: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    db_path = output_dir / "writelab_synthetic_e2e.sqlite"
    zip_path = output_dir / "writelab-handoff.zip"
    validation_path = output_dir / "VALIDATION_OUTPUT.json"
    api_probe_path = output_dir / "API_PROBE_OUTPUT.json"
    marker_scan_path = output_dir / "MARKER_SCAN_OUTPUT.json"
    probe_output_path = output_dir / "PROBE_OUTPUT.txt"
    temp_db_cleanup_path = output_dir / "TEMP_DB_CLEANUP_CHECK.txt"

    client, engine = _import_writelab_app(writelab_backend, db_path)

    project_resp = client.post(
        "/api/projects",
        json={
            "title": "synthetic-handoff-e2e",
            "paper_type": "journal_article",
            "discipline": "synthetic_governance",
        },
    )
    project_id = project_resp.json().get("id") if project_resp.status_code == 201 else None

    report_resp = client.post(
        "/api/reports/diagnosis",
        json={
            "project_id": project_id,
            "paragraph_version_id": "synthetic-version-1",
            "expected_function": "path_design",
            "actual_function": "path_design",
            "match_score": 86,
            "diagnosis_json": _synthetic_diagnosis_payload(),
        },
    )
    report_id = report_resp.json().get("id") if report_resp.status_code == 201 else None

    endpoint = f"/api/reports/diagnosis/{report_id}/writelab-handoff.zip"
    zip_resp = client.get(endpoint)
    if zip_resp.status_code == 200:
        zip_path.write_bytes(zip_resp.content)

    api_probe = {
        "project_status": project_resp.status_code,
        "report_status": report_resp.status_code,
        "download_status": zip_resp.status_code,
        "project_id": project_id,
        "report_id": report_id,
        "endpoint": endpoint,
        "content_type": zip_resp.headers.get("content-type"),
        "content_disposition": zip_resp.headers.get("content-disposition"),
        "zip_path": str(zip_path),
        "zip_bytes": len(zip_resp.content),
        "synthetic_input_contains_forbidden_marker_count": len(FORBIDDEN_MARKERS),
    }

    if zip_path.exists():
        with zipfile.ZipFile(zip_path, "r") as zf:
            api_probe["zip_namelist"] = sorted(zf.namelist())

    _write_json(api_probe_path, api_probe)

    validation = validate_writelab_handoff(zip_path)
    _write_json(validation_path, validation)

    marker_scan = (
        _scan_zip_for_markers(zip_path)
        if zip_path.exists()
        else {
            "zip_path": str(zip_path),
            "pass": False,
            "marker_count": len(FORBIDDEN_MARKERS),
            "hits_by_label": {},
            "error": "handoff zip was not created",
        }
    )
    _write_json(marker_scan_path, marker_scan)

    engine.dispose()
    removed_database_files: list[str] = []
    for candidate in [db_path, db_path.with_name(db_path.name + "-wal"), db_path.with_name(db_path.name + "-shm")]:
        if candidate.exists():
            candidate.unlink()
            removed_database_files.append(str(candidate))
    temp_db_cleanup_path.write_text(
        "\n".join(
            f"{candidate}: exists={candidate.exists()}"
            for candidate in [db_path, db_path.with_name(db_path.name + "-wal"), db_path.with_name(db_path.name + "-shm")]
        )
        + "\n",
        encoding="utf-8",
    )

    passed = (
        project_resp.status_code == 201
        and report_resp.status_code == 201
        and zip_resp.status_code == 200
        and validation.get("result") == "pass"
        and marker_scan.get("pass") is True
    )

    result = {
        "result": "pass" if passed else "fail",
        "output_dir": str(output_dir),
        "artifacts": {
            "probe_output": str(probe_output_path),
            "api_probe": str(api_probe_path),
            "handoff_zip": str(zip_path),
            "validation": str(validation_path),
            "marker_scan": str(marker_scan_path),
            "temporary_database_cleanup": str(temp_db_cleanup_path),
            "removed_temporary_database_files": removed_database_files,
        },
        "summary": {
            "project_status": project_resp.status_code,
            "report_status": report_resp.status_code,
            "download_status": zip_resp.status_code,
            "validation_result": validation.get("result"),
            "marker_scan_pass": marker_scan.get("pass"),
        },
    }
    _write_json(probe_output_path, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run synthetic WriteLab handoff E2E probe")
    parser.add_argument("--writelab-backend", default=str(DEFAULT_WRITELAB_BACKEND))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args(argv)

    result = run_probe(Path(args.writelab_backend), Path(args.output_dir))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
