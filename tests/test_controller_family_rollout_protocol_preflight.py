from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.controller_family_rollout_protocol_preflight import (
    EXPECTED_PROFILE_COUNT,
    EXPECTED_SPEC_COUNT,
    EXPECTED_WORKLOAD_CELLS,
    run_rollout_protocol_preflight,
    stratum_membership,
)


def test_stratum_membership_splits_explicit_and_unspecified_windows() -> None:
    explicit = stratum_membership({"window_tag": "reveal_plus_4", "task_family": "T4"})
    unspecified = stratum_membership({"window_tag": "mapping_window_unspecified", "task_family": "T5"})

    assert "all_72_specs" in explicit
    assert "explicit_window_subset" in explicit
    assert "mapping_window_unspecified" not in explicit
    assert "mapping_window_unspecified" in unspecified
    assert "task_family_T5" in unspecified


def test_run_rollout_protocol_preflight_writes_no_rollout_workload(tmp_path: Path) -> None:
    summary = run_rollout_protocol_preflight(output_dir=tmp_path)

    protocol = read_json(tmp_path / "rollout_protocol.json")
    workload_lines = (tmp_path / "workload_matrix.csv").read_text(encoding="utf-8").splitlines()
    persisted_summary = read_json(tmp_path / "summary.json")

    assert summary["passes_public_smoke_gates"] is True
    assert persisted_summary["spec_count"] == EXPECTED_SPEC_COUNT
    assert persisted_summary["profile_count"] == EXPECTED_PROFILE_COUNT
    assert persisted_summary["workload_cell_count"] == EXPECTED_WORKLOAD_CELLS
    assert persisted_summary["explicit_window_subset_count"] > 0
    assert persisted_summary["mapping_window_unspecified_count"] > 0
    assert persisted_summary["hidden_action_target_key_violation_count"] == 0
    assert persisted_summary["guardrail_violation_count"] == 0
    assert persisted_summary["environment_rollout_started"] is False
    assert persisted_summary["training_started"] is False
    assert protocol["strata"]["primary"] == "all_72_specs"
    assert protocol["strata"]["diagnostic"] == "explicit_window_subset"
    assert len(workload_lines) == EXPECTED_WORKLOAD_CELLS + 1
