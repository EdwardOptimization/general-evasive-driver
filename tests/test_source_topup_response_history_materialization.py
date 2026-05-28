from __future__ import annotations

import csv
import json

from autodrift.source_topup_response_history_materialization import (
    materialize_source_topup_response_histories,
)


def _write_csv(path, rows):
    keys = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _source_row(
    *,
    pair_id,
    scenario_id,
    source_run_id,
    source_row_id,
    fault_a,
    fault_b,
    family,
):
    return {
        "pair_id": str(pair_id),
        "scenario_id": scenario_id,
        "seed": "133300",
        "condition_A_fault": fault_a,
        "condition_A_fault_family": family,
        "condition_B_fault": fault_b,
        "condition_B_fault_family": family,
        "fault_family_pair": f"{family}->{family}",
        "source_family": f"{family}->{family}",
        "best_candidate_A": "5",
        "best_candidate_B": "6",
        "best_A_steer": "-0.75",
        "best_A_throttle": "-1.0",
        "best_A_brake": "1.0",
        "best_B_steer": "0.75",
        "best_B_throttle": "-1.0",
        "best_B_brake": "1.0",
        "margin_A_best_A": "0.25",
        "margin_A_best_B": "0.05",
        "margin_B_best_B": "0.24",
        "margin_B_best_A": "0.04",
        "best_A_success": "True",
        "best_B_success": "True",
        "A_using_B_success": "False",
        "B_using_A_success": "False",
        "min_own_margin": "0.24",
        "min_cross_regret": "0.20",
        "near_boundary_margin_le_0_20": "False",
        "high_regret_ge_0_05": "True",
        "source_run_id": source_run_id,
        "source_row_id": str(source_row_id),
        "original_pair_id": str(source_row_id),
        "source_identity": f"{source_run_id}:{source_row_id}",
    }


def _scenario(scenario_id):
    return {
        "scenario_id": scenario_id,
        "seed": "133300",
        "vx": "12.0",
        "vy": "0.0",
        "yaw_rate": "0.0",
        "brake_force": "0.0",
        "drive_force": "3500.0",
        "obstacle_body_x": "10.0",
        "obstacle_body_y": "0.0",
        "obstacle_half_width": "0.5",
        "speed_bin": "medium",
        "obstacle_timing_bin": "late",
        "curvature_bin": "straight",
    }


def test_materialize_source_topup_response_histories_preserves_identity(tmp_path):
    merged = tmp_path / "merged"
    plan = tmp_path / "plan"
    base = tmp_path / "base_source"
    topup = tmp_path / "topup_source"
    run = tmp_path / "run"
    merged.mkdir()
    plan.mkdir()
    base.mkdir()
    topup.mkdir()

    (merged / "summary.json").write_text(
        json.dumps(
            {
                "base_export_run_dir": "runs/m1322_source_repair_corpus_export",
                "topup_source_run_dir": "runs/m1327_source_repair_topup_horizon_corrected_smoke",
                "global_friction_missing": True,
                "halfshaft_undercovered": True,
            }
        ),
        encoding="utf-8",
    )
    (plan / "summary.json").write_text(
        json.dumps({"planned_source_pairs": 2, "planned_pair_probe_groups": 4}),
        encoding="utf-8",
    )
    _write_csv(
        base / "scenario_summary.csv",
        [_scenario("base_s0")],
    )
    _write_csv(
        topup / "scenario_summary.csv",
        [_scenario("topup_s0")],
    )
    _write_csv(
        merged / "all_accepted_source_rows.csv",
        [
            _source_row(
                pair_id=0,
                scenario_id="base_s0",
                source_run_id="m1322_source_repair_corpus_export",
                source_row_id=10,
                fault_a="split_mu_left_low_0p25",
                fault_b="split_mu_right_low_0p25",
                family="left_right_split_mu",
            ),
            _source_row(
                pair_id=1,
                scenario_id="topup_s0",
                source_run_id="m1327_source_repair_topup_horizon_corrected_smoke",
                source_row_id=11,
                fault_a="front_left_brake_loss_0p0",
                fault_b="front_right_brake_loss_0p0",
                family="single_wheel_brake_pull",
            ),
        ],
    )
    _write_csv(
        plan / "planned_source_pairs.csv",
        [
            {"pair_id": "0", "fold": "0", "margin_bucket": "near_020"},
            {"pair_id": "1", "fold": "1", "margin_bucket": "positive"},
        ],
    )

    summary = materialize_source_topup_response_histories(
        merged_source_run_dir=merged,
        expansion_plan_run_dir=plan,
        base_source_run_dir=base,
        topup_source_run_dir=topup,
        run_dir=run,
        history_length=3,
    )

    assert summary["result_class"] == "source_topup_response_history_materialization_pass"
    assert summary["source_pair_rows"] == 2
    assert summary["history_prefix_rows"] == 8
    assert summary["history_frame_rows"] == 24
    assert summary["history_intervention_rows"] == 8
    assert summary["wrong_history_pair_rows"] == 8
    assert summary["scenario_lookup_missing_count"] == 0
    assert summary["fault_lookup_missing_count"] == 0
    assert summary["source_identity_duplicate_count"] == 0
    assert summary["source_identity_metadata_preserved"] is True
    assert summary["wrong_history_valid_count"] == 8
    assert summary["actor_view_history_all_finite"] is True
    assert summary["forbidden_actor_view_history_columns"] == []
    assert summary["global_friction_missing"] is True
    assert summary["halfshaft_undercovered"] is True
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False

    with (run / "history_frame_rows.csv").open(newline="", encoding="utf-8") as handle:
        first_frame = next(csv.DictReader(handle))
    assert first_frame["source_identity"] == "m1322_source_repair_corpus_export:10"
    assert first_frame["source_row_id"] == "10"
    assert first_frame["original_pair_id"] == "10"

    with (run / "source_lineage_rows.csv").open(newline="", encoding="utf-8") as handle:
        lineage_profiles = {row["fault_profile"] for row in csv.DictReader(handle)}
    assert lineage_profiles == {"source_repair_v1", "source_topup_v1"}
