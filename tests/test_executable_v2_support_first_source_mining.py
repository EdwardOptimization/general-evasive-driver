from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows
from autodrift.executable_v2_task_source_metadata_redesign import (
    ROLE_DRIFT_REQUIRED,
    ROLE_STABLE_AEB,
    ROLE_STABLE_AES,
    ROLE_UNAVOIDABLE,
    SUPPORTED,
    UNSUPPORTED,
)
from autodrift import executable_v2_support_first_source_mining as mining


def _candidate(
    source: str,
    role: str,
    *,
    distance: float,
    speed: float = 20.0,
    mu: float = 1.0,
    half_width: float = 0.3,
    recovery_horizon_required: bool = False,
    mitigation_metric_contract_present: bool = False,
    require_aeb_infeasible: bool | None = None,
) -> dict[str, object]:
    if require_aeb_infeasible is None:
        require_aeb_infeasible = role == ROLE_STABLE_AES
    return {
        "candidate_source_id": source,
        "source_v1_bounded_panel_spec_id": source,
        "source_scenario_spec_id": f"{source}_scenario",
        "source_family_id": "family",
        "source_role_semantics": role,
        "source_required_label": mining.required_label_for_role(role),
        "source_allowed_labels": mining.required_label_for_role(role),
        "require_aeb_infeasible": require_aeb_infeasible,
        "profile_name": "p0",
        "profile_group": "g0",
        "speed_ref": speed,
        "mu": mu,
        "friction_step_enabled": False,
        "obstacle_distance_min": distance,
        "obstacle_distance_max": distance,
        "obstacle_distance_count": 1,
        "obstacle_half_width_min": half_width,
        "obstacle_half_width_max": half_width,
        "obstacle_half_width_count": 1,
        "min_accepted_cells": 1,
        "recovery_horizon_required": recovery_horizon_required,
        "mitigation_metric_contract_present": mitigation_metric_contract_present,
    }


def _run(tmp_path: Path, rows: list[dict[str, object]]) -> dict[str, object]:
    return mining.run_support_first_source_mining(
        candidate_rows=rows,
        output_dir=tmp_path / "out",
        claim_boundary_context="implementation_only",
    )


def test_stable_aes_candidate_is_supported_and_metadata_compatible(tmp_path: Path) -> None:
    summary = _run(tmp_path, [_candidate("aes", ROLE_STABLE_AES, distance=18.0)])

    assert summary["candidate_source_count"] == 1
    assert summary["supported_source_count"] == 1
    assert summary["stable_aes_supported_source_count"] == 1
    assert summary["materialized_row_count"] == 0
    assert summary["guardrail_violation_count"] == 0

    materialization = (tmp_path / "out" / "support_first_materialization_admissibility_input.csv").read_text()
    assert ROLE_STABLE_AES in materialization
    assert SUPPORTED in materialization
    assert "True" in materialization

    payload = read_json(tmp_path / "out" / "summary.json")
    assert payload["contract_id"] == mining.CONTRACT_ID


def test_aeb_cell_does_not_certify_stable_aes_but_supports_stable_aeb(tmp_path: Path) -> None:
    summary = _run(
        tmp_path,
        [
            _candidate("aes", ROLE_STABLE_AES, distance=80.0),
            _candidate("aeb", ROLE_STABLE_AEB, distance=80.0, require_aeb_infeasible=False),
        ],
    )

    assert summary["candidate_source_count"] == 2
    assert summary["supported_source_count"] == 1
    assert summary["stable_aes_supported_source_count"] == 0
    assert summary["stable_aeb_supported_source_count"] == 1

    blocked = (tmp_path / "out" / "support_first_blocked_candidates.csv").read_text()
    assert ROLE_STABLE_AES in blocked
    assert mining.REJECT_AEB_FEASIBLE in (tmp_path / "out" / "support_first_profile_support.csv").read_text()


def test_drift_required_role_is_separate_from_stable_aes(tmp_path: Path) -> None:
    summary = _run(
        tmp_path,
        [
            _candidate("aes", ROLE_STABLE_AES, distance=12.0),
            _candidate("drift", ROLE_DRIFT_REQUIRED, distance=12.0, recovery_horizon_required=True),
        ],
    )

    assert summary["stable_aes_supported_source_count"] == 0
    assert summary["drift_required_supported_source_count"] == 1

    support = (tmp_path / "out" / "support_first_profile_support.csv").read_text()
    assert ROLE_DRIFT_REQUIRED in support
    assert ROLE_STABLE_AES in support


def test_unavoidable_requires_mitigation_metric_contract(tmp_path: Path) -> None:
    summary = _run(
        tmp_path,
        [
            _candidate("unavoidable_missing", ROLE_UNAVOIDABLE, distance=8.0),
            _candidate(
                "unavoidable",
                ROLE_UNAVOIDABLE,
                distance=8.0,
                mitigation_metric_contract_present=True,
            ),
        ],
    )

    assert summary["unavoidable_supported_source_count"] == 1
    assert summary["unsupported_source_count"] == 1

    profile_support = (tmp_path / "out" / "support_first_profile_support.csv").read_text()
    assert mining.REJECT_MITIGATION_CONTRACT in profile_support


def test_cli_loads_csv_and_writes_claim_boundary(tmp_path: Path) -> None:
    candidates = tmp_path / "candidates.csv"
    write_csv_rows(candidates, [_candidate("aes", ROLE_STABLE_AES, distance=18.0)])

    summary = mining.run_support_first_source_mining_from_paths(
        candidate_rows_path=candidates,
        output_dir=tmp_path / "out",
        claim_boundary_context="project_artifact_execution",
    )

    assert summary["supported_source_count"] == 1
    boundary = (tmp_path / "out" / "support_first_claim_boundary.csv").read_text()
    assert "project_artifact_source_mining_result,True" in boundary
    assert "materialized_executable_v2_rows_generated,False" in boundary


def test_claim_boundary_blocks_ranking_and_materialization_claims() -> None:
    rows = mining.claim_boundary_rows("implementation_only")
    by_claim = {row["claim"]: row for row in rows}

    assert by_claim["support_first_source_mining_helper"]["admissible"] is True
    assert by_claim["materialized_executable_v2_rows_generated"]["admissible"] is False
    assert by_claim["controller_family_ranking"]["admissible"] is False
    assert by_claim["project_artifact_source_mining_result"]["admissible"] is False


def test_multi_profile_stable_roles_require_all_profiles_supported(tmp_path: Path) -> None:
    supported = _candidate("mixed", ROLE_STABLE_AES, distance=18.0)
    unsupported = {
        **_candidate("mixed", ROLE_STABLE_AES, distance=80.0),
        "profile_name": "p1",
    }
    summary = _run(tmp_path, [supported, unsupported])

    assert summary["stable_aes_supported_source_count"] == 0
    assert summary["unsupported_source_count"] == 1
    materialization = (tmp_path / "out" / "support_first_materialization_admissibility_input.csv").read_text()
    assert UNSUPPORTED in materialization


def test_insufficient_accepted_cells_gets_explicit_failure_reason(tmp_path: Path) -> None:
    row = {
        **_candidate("thin", ROLE_STABLE_AES, distance=18.0),
        "min_accepted_cells": 2,
    }
    summary = _run(tmp_path, [row])

    assert summary["supported_source_count"] == 0
    profile_support = (tmp_path / "out" / "support_first_profile_support.csv").read_text()
    materialization = (tmp_path / "out" / "support_first_materialization_admissibility_input.csv").read_text()
    assert mining.FAIL_INSUFFICIENT_ACCEPTED in profile_support
    assert mining.FAIL_INSUFFICIENT_ACCEPTED in materialization


def test_diversity_summary_counts_exact_speed_and_mu_values() -> None:
    rows = [
        _candidate("a", ROLE_STABLE_AES, distance=18.0, speed=10.0, mu=1.0),
        _candidate("b", ROLE_STABLE_AES, distance=18.0, speed=14.0, mu=1.15),
    ]
    diversity = mining.diversity_summary(rows)

    assert diversity["speed_bucket_count"] == 2
    assert diversity["mu_bucket_count"] == 2
