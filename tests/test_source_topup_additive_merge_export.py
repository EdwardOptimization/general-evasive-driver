from __future__ import annotations

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.source_topup_additive_merge_export import export_source_topup_additive_merge


def _accepted_row(pair_id: int, *, scenario_id: str, family: str) -> dict[str, object]:
    return {
        "pair_id": pair_id,
        "scenario_id": scenario_id,
        "seed": pair_id + 100,
        "condition_A_fault": f"{family}_left",
        "condition_A_fault_family": family,
        "condition_A_fault_severity": "sev",
        "condition_A_corner_or_side_variant": "left",
        "condition_A_onset_timing_bin": "persistent",
        "condition_A_curvature_bin": "straight",
        "condition_A_params_override": "",
        "condition_B_fault": f"{family}_right",
        "condition_B_fault_family": family,
        "condition_B_fault_severity": "sev",
        "condition_B_corner_or_side_variant": "right",
        "condition_B_onset_timing_bin": "persistent",
        "condition_B_curvature_bin": "straight",
        "condition_B_params_override": "",
        "fault_family_pair": f"{family}->{family}",
        "severity_pair": "sev->sev",
        "corner_or_side_variant_pair": "left->right",
        "onset_timing_bin_pair": "persistent->persistent",
        "curvature_bin_pair": "straight->straight",
        "obstacle_body_x": 10.0,
        "obstacle_body_y": 0.0,
        "obstacle_half_width": 0.6,
        "speed_bin": "medium",
        "obstacle_timing_bin": "late",
        "scenario_curvature_bin": "straight",
        "best_A_template": "left_steer_release",
        "best_B_template": "right_steer_release",
        "accepted": True,
        "acceptance_reason": "capability_separable",
        "rejection_reason": "accepted",
        "best_candidate_A": 1,
        "best_candidate_B": 2,
        "best_action_l2": 1.0,
        "margin_A_best_A": 0.04,
        "margin_A_best_B": -0.02,
        "margin_B_best_B": 0.08,
        "margin_B_best_A": -0.03,
        "cross_regret_A": 0.06,
        "cross_regret_B": 0.11,
        "best_A_success": True,
        "best_B_success": True,
        "A_using_B_success": False,
        "B_using_A_success": False,
    }


def test_additive_merge_export_adds_source_identity_and_diagnostics(tmp_path):
    base_dir = tmp_path / "m1322_source_repair_corpus_export"
    topup_dir = tmp_path / "m1327_source_repair_topup_horizon_corrected_smoke"
    out_dir = tmp_path / "merged"
    base_dir.mkdir()
    topup_dir.mkdir()

    write_json(base_dir / "summary.json", {"exported_accepted_rows": 1})
    base_row = _accepted_row(1, scenario_id="base_scenario", family="single_wheel_brake_pull")
    base_row.update(
        {
            "speed": 16.0,
            "min_own_margin": 0.04,
            "min_cross_regret": 0.06,
            "near_boundary_margin_le_0_05": True,
            "near_boundary_margin_le_0_10": True,
            "near_boundary_margin_le_0_20": True,
            "high_regret_ge_0_05": True,
            "high_regret_ge_0_10": False,
            "source_family": "single_wheel_brake_pull->single_wheel_brake_pull",
        }
    )
    write_csv_rows(base_dir / "all_accepted_source_rows.csv", [base_row])

    write_json(topup_dir / "summary.json", {"accepted_separable_pairs": 1})
    topup_row = _accepted_row(2, scenario_id="topup_scenario", family="load_cg_perturbation")
    write_csv_rows(topup_dir / "accepted_separable_pairs.csv", [topup_row])
    write_csv_rows(topup_dir / "scenario_summary.csv", [{"scenario_id": "topup_scenario", "vx": 18.0}])

    summary = export_source_topup_additive_merge(
        base_export_run_dir=base_dir,
        topup_source_run_dir=topup_dir,
        run_dir=out_dir,
        family_cap=40,
    )

    assert summary["merged_source_identity_rows"] == 2
    assert summary["source_identity_duplicate_count"] == 0
    assert summary["family_balanced_rows"] == 2
    assert summary["accepted_fault_family_pairs"] == 2
    assert summary["global_friction_missing"] is True
    assert read_json(out_dir / "summary.json")["merged_source_identity_rows"] == 2

    merged_rows = (out_dir / "all_accepted_source_rows.csv").read_text(encoding="utf-8")
    assert "source_identity" in merged_rows
    assert "original_pair_id" in merged_rows
    assert "m1322_source_repair_corpus_export:1" in merged_rows
    assert "m1327_source_repair_topup_horizon_corrected_smoke:2" in merged_rows
    assert "\n0," in merged_rows
    assert "\n1," in merged_rows

    undercovered_rows = (out_dir / "inactive_or_undercovered_families.csv").read_text(encoding="utf-8")
    assert "global_friction_step->global_friction_step" in undercovered_rows
