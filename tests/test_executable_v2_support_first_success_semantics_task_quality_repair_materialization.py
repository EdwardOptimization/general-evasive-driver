from __future__ import annotations

import csv
import json
from pathlib import Path

from autodrift.executable_v2_support_first_success_semantics_task_quality_repair_materialization import (
    REPAIR_VARIANTS,
    diagnostic_flags,
    materialize,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_diagnostic_flags_detect_offtrack_after_clearance() -> None:
    flags = diagnostic_flags(
        {
            "collision": "False",
            "min_clearance_margin": "0.3",
            "termination_reason": "off_track",
            "first_obstacle_pass_time_s": "1.0",
            "time_to_first_off_track_s": "1.2",
            "recovery_success": "False",
            "controlled_drift_recovery_success": "True",
        }
    )

    assert flags["obstacle_clearance_pass"]
    assert not flags["road_containment_pass"]
    assert flags["obstacle_pass_before_offtrack"]
    assert flags["offtrack_after_clearance"]
    assert flags["controlled_recovery_pass"]


def test_materialize_repair_matrix_preserves_profiles_and_baseline(tmp_path: Path) -> None:
    workload = tmp_path / "workload.csv"
    episodes = tmp_path / "episodes.csv"
    localization = tmp_path / "summary.json"
    output = tmp_path / "out"

    workload_rows = [
        {
            "workload_id": "w0",
            "support_first_workload_id": "w0",
            "support_first_v2_panel_spec_id": "s0",
            "controller_profile_name": "L0_current_masked",
            "profile_name": "L0_current_masked",
            "role_panel_id": "stable_aeb",
            "v2_role_surface_id": "stable_aeb::steady_surface",
            "profile_specific_tuning": "False",
        },
        {
            "workload_id": "w1",
            "support_first_workload_id": "w1",
            "support_first_v2_panel_spec_id": "s0",
            "controller_profile_name": "L3_online_gru",
            "profile_name": "L3_online_gru",
            "role_panel_id": "drift_required_recovery",
            "v2_role_surface_id": "drift_required_recovery::steady_surface",
            "profile_specific_tuning": "False",
        },
    ]
    episode_rows = [
        {
            "role_panel_id": "stable_aeb",
            "collision": "False",
            "min_clearance_margin": "0.2",
            "termination_reason": "off_track",
            "first_obstacle_pass_time_s": "nan",
            "time_to_first_off_track_s": "1.0",
        },
        {
            "role_panel_id": "drift_required_recovery",
            "collision": "True",
            "min_clearance_margin": "-0.1",
            "termination_reason": "collision",
            "first_obstacle_pass_time_s": "nan",
            "time_to_first_off_track_s": "nan",
        },
    ]
    _write_csv(workload, workload_rows)
    _write_csv(episodes, episode_rows)
    localization.write_text(
        json.dumps(
            {
                "result_class": "support_first_outcome_localization_pass",
                "outcome_dominance_class": "diffuse_support_first_outcome_dominance",
                "dominant_slice_count": 10,
            }
        ),
        encoding="utf-8",
    )

    summary = materialize(
        workload_matrix=workload,
        episode_rows_path=episodes,
        localization_summary_path=localization,
        output_dir=output,
        target_workload_row_count=2,
        target_repair_variant_count=len(REPAIR_VARIANTS),
        next_blocker="m-test",
    )

    assert summary["result_class"] == "support_first_success_semantics_task_quality_repair_materialization_pass"
    assert summary["workload_row_count"] == 2
    assert summary["repair_matrix_row_count"] == 2 * len(REPAIR_VARIANTS)
    assert summary["original_baseline_retained"]
    assert summary["all_controller_profiles_preserved"]
    assert summary["guardrail_violation_count"] == 0
    assert (output / "summary.json").exists()
    assert (output / "repair_variant_matrix.csv").exists()
    assert (output / "role_semantics_spec.json").exists()
