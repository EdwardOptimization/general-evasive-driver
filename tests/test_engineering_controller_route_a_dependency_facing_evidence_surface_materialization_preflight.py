import csv
import json
from pathlib import Path

from autodrift.engineering_controller_route_a_dependency_facing_evidence_surface_materialization_preflight import (
    DECISION_FAIL,
    DECISION_PASS,
    NEXT_ID,
    write_preflight_artifacts,
)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_parent_docs(tmp_path: Path) -> dict[str, Path]:
    docs = {
        "m2912_design": tmp_path / "docs" / "m2912.md",
        "m2911_synthesis": tmp_path / "docs" / "m2911.md",
        "m2910_synthesis": tmp_path / "docs" / "m2910.md",
        "m2879_synthesis": tmp_path / "docs" / "m2879.md",
        "m2883_design": tmp_path / "docs" / "m2883.md",
    }
    for name, path in docs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"{name} fixture\n", encoding="utf-8")
    return docs


def test_m2913_materializes_dependency_facing_surface(tmp_path: Path) -> None:
    docs = _write_parent_docs(tmp_path)
    output_dir = tmp_path / "runs" / "m2913"
    follow_up_manifest = tmp_path / "experiments" / "manifests" / "m2914.json"

    summary = write_preflight_artifacts(
        output_dir=output_dir,
        follow_up_manifest=follow_up_manifest,
        **docs,
    )

    assert summary["status_pass"] is True
    assert summary["decision"] == DECISION_PASS
    assert summary["route_context_row_count"] == 5
    assert summary["candidate_family_row_count"] == 5
    assert summary["exclusion_family_row_count"] == 6
    assert summary["denominator_policy_row_count"] == 6
    assert summary["failure_taxonomy_row_count"] == 7
    assert summary["claim_made_count"] == 0
    assert summary["claim_allowed_count"] == 0
    assert summary["ordinary_engineering_candidate_family_count"] == 1

    candidate_rows = _read_rows(output_dir / "candidate_family_rows.csv")
    route_context_rows = _read_rows(output_dir / "route_context_rows.csv")
    gate_rows = _read_rows(output_dir / "gate_rows.csv")
    claim_rows = _read_rows(output_dir / "claim_boundary_rows.csv")

    assert {row["family_name"] for row in candidate_rows} >= {
        "route_a_source_diverse_closed_loop_diagnostics",
        "route_b_source_insufficient_context",
        "route_c_source_unavailable_context",
    }
    assert {row["paper_denominator_allowed"] for row in route_context_rows} == {"False"}
    assert {row["claim_made"] for row in claim_rows} == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert follow_up_manifest.exists()
    assert _read_json(follow_up_manifest)["id"] == NEXT_ID


def test_m2913_fails_closed_when_parent_artifact_missing(tmp_path: Path) -> None:
    docs = _write_parent_docs(tmp_path)
    docs["m2910_synthesis"].unlink()

    summary = write_preflight_artifacts(
        output_dir=tmp_path / "runs" / "m2913",
        follow_up_manifest=tmp_path / "experiments" / "manifests" / "m2914.json",
        **docs,
    )

    assert summary["status_pass"] is False
    assert summary["decision"] == DECISION_FAIL
    assert summary["parent_artifact_missing_count"] == 1
    gate_rows = _read_rows(tmp_path / "runs" / "m2913" / "gate_rows.csv")
    parent_gate = [row for row in gate_rows if row["gate_family"] == "parent_artifacts_exist"][0]
    assert parent_gate["status_pass"] == "False"
