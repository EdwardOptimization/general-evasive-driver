from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json
from autodrift import executable_v2_task_source_metadata_redesign as redesign


def _source(source: str, role: str = redesign.ROLE_STABLE_AES) -> dict[str, object]:
    return {
        "source_v1_bounded_panel_spec_id": source,
        "source_scenario_spec_id": f"{source}_scenario",
        "source_role_semantics": role,
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
    }


def _profile(source: str, *, feasible: bool, accepted: int, dominant_label: str) -> dict[str, object]:
    return {
        "source_v1_bounded_panel_spec_id": source,
        "source_scenario_spec_id": f"{source}_scenario",
        "v2_panel_spec_id": f"{source}::p0",
        "profile_name": "p0",
        "feasible": feasible,
        "accepted_cell_count": accepted,
        "dominant_label": dominant_label,
        "dominant_reject_reason": "" if feasible else "aeb_feasible_rejected",
    }


def _label(source: str, label: str, count: int) -> dict[str, object]:
    return {
        "source_v1_bounded_panel_spec_id": source,
        "source_scenario_spec_id": f"{source}_scenario",
        "label": label,
        "count": count,
    }


def _run(
    tmp_path: Path,
    *,
    source_rows: list[dict[str, object]],
    profiles: list[dict[str, object]],
    labels: list[dict[str, object]] | None = None,
    context: str = "implementation_only",
) -> dict[str, object]:
    return redesign.run_task_source_metadata_redesign(
        source_rows=source_rows,
        profile_summary_rows=profiles,
        label_count_rows=labels or [],
        reject_reason_rows=[],
        output_dir=tmp_path / "out",
        support_evidence_artifact="support.csv",
        claim_boundary_context=context,
    )


def test_blocks_stable_aes_when_support_has_zero_accepted_cells(tmp_path: Path) -> None:
    summary = _run(
        tmp_path,
        source_rows=[_source("src")],
        profiles=[_profile("src", feasible=False, accepted=0, dominant_label="aeb_feasible")],
        labels=[_label("src", "aeb_feasible", 8)],
    )

    assert summary["supported_source_count"] == 0
    assert summary["unsupported_source_count"] == 1
    assert summary["materialization_blocked_source_count"] == 1

    blocked = (tmp_path / "out" / "task_source_blocked_sources.csv").read_text()
    assert redesign.FAIL_LABEL_ROLE_MISMATCH in blocked
    assert "False" in blocked


def test_drift_required_evidence_does_not_certify_stable_aes(tmp_path: Path) -> None:
    summary = _run(
        tmp_path,
        source_rows=[_source("src", role=redesign.ROLE_STABLE_AES)],
        profiles=[_profile("src", feasible=False, accepted=0, dominant_label="drift_required")],
        labels=[_label("src", "drift_required", 5)],
    )

    assert summary["supported_source_count"] == 0
    assert summary["materialization_admissible_source_count"] == 0
    support = (tmp_path / "out" / "task_source_support_contract.csv").read_text()
    assert redesign.ROLE_STABLE_AES in support
    assert redesign.FAIL_LABEL_ROLE_MISMATCH in support


def test_supported_stable_aes_admits_materialization_and_preserves_controls(tmp_path: Path) -> None:
    summary = _run(
        tmp_path,
        source_rows=[_source("src")],
        profiles=[
            _profile("src", feasible=True, accepted=2, dominant_label="aes_feasible"),
            {
                **_profile("src", feasible=True, accepted=1, dominant_label="aes_feasible"),
                "v2_panel_spec_id": "src::p1",
                "profile_name": "p1",
            },
        ],
        labels=[_label("src", "aes_feasible", 3)],
    )

    assert summary["supported_source_count"] == 1
    assert summary["materialization_admissible_source_count"] == 1
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["ranking_admissible_by_default_count"] == 0
    assert summary["guardrail_violation_count"] == 0

    payload = read_json(tmp_path / "out" / "summary.json")
    assert payload["contract_id"] == redesign.CONTRACT_ID


def test_missing_support_evidence_is_unknown_and_blocks_materialization(tmp_path: Path) -> None:
    summary = _run(
        tmp_path,
        source_rows=[_source("src")],
        profiles=[],
        labels=[],
    )

    assert summary["unknown_source_count"] == 1
    assert summary["materialization_blocked_source_count"] == 1
    blocked = (tmp_path / "out" / "task_source_blocked_sources.csv").read_text()
    assert redesign.FAIL_MISSING_EVIDENCE in blocked
    assert redesign.BLOCK_UNKNOWN in blocked


def test_can_derive_source_rows_from_profile_summary() -> None:
    rows = redesign.source_rows_from_profile_summary(
        profile_summary_rows=[
            _profile("src", feasible=False, accepted=0, dominant_label="aeb_feasible"),
            {
                **_profile("src", feasible=False, accepted=0, dominant_label="aeb_feasible"),
                "v2_panel_spec_id": "src::p1",
            },
        ],
        default_role=redesign.ROLE_STABLE_AES,
    )

    assert rows == [
        {
            "source_v1_bounded_panel_spec_id": "src",
            "source_scenario_spec_id": "src_scenario",
            "source_role_semantics": redesign.ROLE_STABLE_AES,
            "labels_enter_actor_input": False,
            "v2_ranking_admissible_by_default": False,
        }
    ]


def test_claim_boundary_is_context_aware() -> None:
    implementation = {row["claim"]: row for row in redesign.claim_boundary_rows("implementation_only")}
    execution = {row["claim"]: row for row in redesign.claim_boundary_rows("project_artifact_execution")}
    audit = {row["claim"]: row for row in redesign.claim_boundary_rows("result_audit")}
    synthesis = {row["claim"]: row for row in redesign.claim_boundary_rows("branch_synthesis")}

    assert implementation["metadata_helper_implementation"]["admissible"] is True
    assert implementation["project_artifact_execution"]["admissible"] is False
    assert execution["project_artifact_execution"]["admissible"] is True
    assert audit["result_audit"]["admissible"] is True
    assert synthesis["result_audit"]["admissible"] is True
    assert synthesis["controller_family_ranking"]["admissible"] is False
