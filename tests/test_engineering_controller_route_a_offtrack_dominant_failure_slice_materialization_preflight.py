from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_route_a_offtrack_dominant_failure_slice_materialization_preflight as m2925


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _execution_row(
    index: int,
    *,
    termination_reason: str,
    success: bool,
    collision: bool,
    source_milestone: str,
    task_family: str,
    checkpoint_path: str,
    env_template_family: str,
    window_tag: str,
    overshoot: float = 0.0,
    time_to_offtrack: float = 0.0,
) -> dict[str, object]:
    return {
        "seed": 292500 + index,
        "policy": "checkpoint",
        "steps": 20 + index,
        "collision": collision,
        "termination_reason": termination_reason,
        "completion_reason": termination_reason,
        "min_clearance_margin": 1.0 + index,
        "return": 10.0 + index,
        "success": success,
        "action_rate_mean": 0.1,
        "high_sideslip_fraction": 0.0,
        "lateral_rmse": 1.0 + index / 10.0,
        "speed_mean": 8.0 + index,
        "max_off_track_overshoot": overshoot,
        "off_track_severity_proxy": overshoot,
        "time_to_first_off_track_s": time_to_offtrack,
        "workload_id": f"task-{index}::L3_online_gru",
        "task_source_id": f"task-{index}",
        "profile_name": "L3_online_gru",
        "task_family": task_family,
        "source_milestone": source_milestone,
        "source_family": "mock_source_family",
        "source_edge": "mock_edge",
        "source_row_id": f"source-row-{index}",
        "env_template_family": env_template_family,
        "window_tag": window_tag,
        "profile_env_history_length": 1,
        "checkpoint_path": checkpoint_path,
        "execution_candidate_id": f"candidate-{index:04d}",
        "resolution_id": f"resolution-{index:04d}",
        "hidden_oracle_actor_input_required": False,
        "future_target_actor_input_required": False,
        "route_labels_actor_visible": False,
        "source_labels_actor_visible": False,
        "diagnostic_labels_actor_visible": False,
        "success_progress_labels_actor_visible": False,
        "verdict_labels_actor_visible": False,
        "driver_performance_claim_made": False,
        "paper_claim_made": False,
        "level3_self_id_claim_made": False,
        "diagnostic_only_no_verdict": True,
    }


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    m2919_dir = root / "m2919"
    m2922_dir = root / "m2922"
    rows = [
        _execution_row(
            1,
            termination_reason="off_track",
            success=False,
            collision=False,
            source_milestone="m2737",
            task_family="T4",
            checkpoint_path="runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            env_template_family="env_a",
            window_tag="window_a",
            overshoot=0.01,
            time_to_offtrack=1.5,
        ),
        _execution_row(
            2,
            termination_reason="off_track",
            success=False,
            collision=False,
            source_milestone="m2737",
            task_family="T5",
            checkpoint_path="runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            env_template_family="env_b",
            window_tag="window_b",
            overshoot=0.05,
            time_to_offtrack=2.0,
        ),
        _execution_row(
            3,
            termination_reason="off_track",
            success=False,
            collision=False,
            source_milestone="m2746",
            task_family="T5",
            checkpoint_path="runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt",
            env_template_family="env_b",
            window_tag="window_b",
            overshoot=0.1,
            time_to_offtrack=3.0,
        ),
        _execution_row(
            4,
            termination_reason="",
            success=True,
            collision=False,
            source_milestone="m2737",
            task_family="T4",
            checkpoint_path="runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            env_template_family="env_a",
            window_tag="window_a",
        ),
        _execution_row(
            5,
            termination_reason="speed_too_low",
            success=False,
            collision=False,
            source_milestone="m2746",
            task_family="T4",
            checkpoint_path="runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt",
            env_template_family="env_c",
            window_tag="window_c",
        ),
    ]
    write_csv_rows(m2919_dir / "bounded_execution_rows.csv", rows)
    write_json(m2922_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(
        m2922_dir / "guardrail_context_rows.csv",
        [
            {"guardrail_source": "m2922", "guardrail_family": "route_b_context_only", "source_row_id": "route-b", "execution_run": False},
            {"guardrail_source": "m2922", "guardrail_family": "route_c_source_unavailable_rows", "source_row_id": "route-c", "execution_run": False},
            {"guardrail_source": "m2922", "guardrail_family": "m2877_fixed_post_package_rows", "source_row_id": "m2877", "execution_run": False},
        ],
    )
    for name in ["actor_contract_guard_rows.csv", "claim_boundary_rows.csv", "gate_matrix.csv"]:
        write_csv_rows(m2922_dir / name, [{"id": "placeholder", "status_pass": True}])

    m2923_audit = root / "m2923.md"
    m2924_design = root / "m2924.md"
    m2923_audit.write_text("M2923 accepts M2922 complete and claim-safe.\n", encoding="utf-8")
    m2924_design.write_text(m2925.MILESTONE_ID + "\n", encoding="utf-8")
    return {
        "m2919_dir": m2919_dir,
        "m2922_dir": m2922_dir,
        "m2923_audit": m2923_audit,
        "m2924_design": m2924_design,
    }


def test_checkpoint_and_band_classifiers() -> None:
    public_row = {"checkpoint_path": "runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt"}
    m2655_row = {"checkpoint_path": "runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt"}
    assert m2925.checkpoint_context(public_row) == "public_pilot_l3_checkpoint"
    assert m2925.checkpoint_context(m2655_row) == "m2655_mitigation_preserving_checkpoint"
    assert m2925.offtrack_severity_band({"off_track_severity_proxy": 0.01}) == "low_overshoot_le_0p02"
    assert m2925.offtrack_severity_band({"off_track_severity_proxy": 0.05}) == "medium_overshoot_le_0p08"
    assert m2925.offtrack_severity_band({"off_track_severity_proxy": 0.1}) == "high_overshoot_gt_0p08"
    assert m2925.time_to_offtrack_band({"time_to_first_off_track_s": 1.5}) == "early_le_1p75s"
    assert m2925.time_to_offtrack_band({"time_to_first_off_track_s": 2.0}) == "mid_le_2p5s"
    assert m2925.time_to_offtrack_band({"time_to_first_off_track_s": 3.0}) == "late_gt_2p5s"


def test_run_materialization_writes_offtrack_slices_without_execution(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m2925, "EXPECTED_TOTAL_ROW_COUNT", 5)
    monkeypatch.setattr(m2925, "EXPECTED_OFFTRACK_COUNT", 3)
    monkeypatch.setattr(m2925, "EXPECTED_NON_OFFTRACK_CONTEXT_COUNT", 2)
    monkeypatch.setattr(m2925, "EXPECTED_OFFTRACK_SOURCE_COUNTS", {"m2737": 2, "m2746": 1})
    monkeypatch.setattr(m2925, "EXPECTED_OFFTRACK_TASK_COUNTS", {"T4": 1, "T5": 2})
    monkeypatch.setattr(
        m2925,
        "EXPECTED_CHECKPOINT_CONTEXT_COUNTS",
        {"public_pilot_l3_checkpoint": 1, "m2655_mitigation_preserving_checkpoint": 2},
    )
    monkeypatch.setattr(m2925, "EXPECTED_ENVIRONMENT_COUNTS", {"env_a": 1, "env_b": 2})
    monkeypatch.setattr(m2925, "EXPECTED_WINDOW_COUNTS", {"window_a": 1, "window_b": 2})
    monkeypatch.setattr(
        m2925,
        "EXPECTED_OVERSHOOT_BAND_COUNTS",
        {"low_overshoot_le_0p02": 1, "medium_overshoot_le_0p08": 1, "high_overshoot_gt_0p08": 1},
    )
    monkeypatch.setattr(
        m2925,
        "EXPECTED_TIME_BAND_COUNTS",
        {"early_le_1p75s": 1, "mid_le_2p5s": 1, "late_gt_2p5s": 1},
    )
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2925"
    doc_path = tmp_path / "m2925.md"
    follow_up = tmp_path / "m2926.json"

    summary = m2925.run_offtrack_dominant_failure_slice_materialization_preflight(
        m2922_dir=paths["m2922_dir"],
        m2919_dir=paths["m2919_dir"],
        m2923_audit=paths["m2923_audit"],
        m2924_design=paths["m2924_design"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["execution_row_count"] == 5
    assert summary["offtrack_row_count"] == 3
    assert summary["non_offtrack_context_row_count"] == 2
    assert summary["offtrack_source_counts"] == {"m2737": 2, "m2746": 1}
    assert summary["offtrack_task_counts"] == {"T4": 1, "T5": 2}
    assert summary["offtrack_overshoot_band_counts"] == {
        "high_overshoot_gt_0p08": 1,
        "low_overshoot_le_0p02": 1,
        "medium_overshoot_le_0p08": 1,
    }
    assert summary["offtrack_time_band_counts"] == {
        "early_le_1p75s": 1,
        "late_gt_2p5s": 1,
        "mid_le_2p5s": 1,
    }
    assert summary["environment_reset_run"] is False
    assert summary["policy_rollout_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert doc_path.exists()
    assert read_json(follow_up)["id"] == m2925.NEXT_ID

    assert len(_read_csv(output_dir / "offtrack_slice_rows.csv")) == 3
    assert len(_read_csv(output_dir / "non_offtrack_context_rows.csv")) == 2
    assert len(_read_csv(output_dir / "offtrack_severity_slice_rows.csv")) == 6
    assert {row["m2925_execution_performed"] for row in _read_csv(output_dir / "offtrack_slice_rows.csv")} == {"False"}
    assert {row["ranking_claim_made"] for row in _read_csv(output_dir / "offtrack_source_slice_rows.csv")} == {"False"}
    assert {row["status_pass"] for row in _read_csv(output_dir / "gate_matrix.csv")} == {"True"}
