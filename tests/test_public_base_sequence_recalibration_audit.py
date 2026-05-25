import csv

from autodrift.artifacts import write_json
from autodrift.public_base_sequence_recalibration_audit import (
    ROUTE_RESIDUAL_FREE,
    ROUTE_TAIL_WEIGHTED,
    ROUTE_TARGET_REGEN,
    choose_route,
    run_public_base_sequence_recalibration_audit,
)


def _write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_choose_route():
    assert (
        choose_route(
            near_base_gap_p10=0.03,
            near_base_gap_deficit_mean=0.01,
            residual_free_gap_p10_threshold=0.021141,
            residual_free_deficit_threshold=0.014809,
            low_tail_count=0,
            distinct_fault_family_pairs=0,
            distinct_variants=0,
            distinct_source_pools=0,
        )
        == ROUTE_RESIDUAL_FREE
    )
    assert (
        choose_route(
            near_base_gap_p10=0.01,
            near_base_gap_deficit_mean=0.02,
            residual_free_gap_p10_threshold=0.021141,
            residual_free_deficit_threshold=0.014809,
            low_tail_count=120,
            distinct_fault_family_pairs=3,
            distinct_variants=1,
            distinct_source_pools=1,
        )
        == ROUTE_TAIL_WEIGHTED
    )
    assert (
        choose_route(
            near_base_gap_p10=0.01,
            near_base_gap_deficit_mean=0.02,
            residual_free_gap_p10_threshold=0.021141,
            residual_free_deficit_threshold=0.014809,
            low_tail_count=20,
            distinct_fault_family_pairs=1,
            distinct_variants=1,
            distinct_source_pools=1,
        )
        == ROUTE_TARGET_REGEN
    )


def test_run_public_base_sequence_recalibration_audit(tmp_path):
    m909_summary = tmp_path / "m909_summary.json"
    m761_summary = tmp_path / "m761_summary.json"
    m909_alpha = tmp_path / "m909_alpha.csv"
    m761_alpha = tmp_path / "m761_alpha.csv"
    objective = tmp_path / "objective.csv"
    run_dir = tmp_path / "run"
    write_json(m909_summary, {"result_class": "v4_sequence_objective_probe_no_gap_lift", "candidate_alpha_count": 0})
    write_json(m761_summary, {"result_class": "v4_sequence_objective_probe_candidate"})
    _write_csv(
        m909_alpha,
        [
            {
                "alpha": 0.02,
                "normal_retention_pass": "True",
                "gap_lift_pass": "False",
                "normal_intervention_gap_p10": 0.007,
                "gap_deficit_mean": 0.017,
                "first_action_drift_from_base_mean": 0.0002,
            }
        ],
    )
    _write_csv(
        m761_alpha,
        [
            {
                "alpha": 0.02,
                "normal_retention_pass": "True",
                "gap_lift_pass": "False",
                "normal_intervention_gap_p10": 0.021,
                "gap_deficit_mean": 0.016,
                "first_action_drift_from_base_mean": 0.00005,
            }
        ],
    )
    rows = []
    for index in range(120):
        rows.append(
            {
                "contrast_group_id": f"g{index}",
                "source_index": index,
                "seed": 10 + index,
                "step": 20,
                "preferred_fault_family": f"p{index % 3}",
                "wrong_fault_family": f"w{index % 3}",
                "fault_family_pair": f"p{index % 3}->w{index % 3}",
                "variant": "zero_command_obs",
                "horizon": 6,
                "source_pool": "public",
                "claim_boundary_level": "current_model_or_proxy",
                "alpha": 0.02,
                "normal_intervention_gap": 0.01,
                "target_gap": 0.04,
                "gap_deficit": 0.03,
                "hard_negative_calibration_loss": 0.001,
            }
        )
    _write_csv(objective, rows)
    summary = run_public_base_sequence_recalibration_audit(
        m909_summary_path=m909_summary,
        m909_alpha_metrics_path=m909_alpha,
        m909_objective_rows_path=objective,
        m761_summary_path=m761_summary,
        m761_alpha_metrics_path=m761_alpha,
        run_dir=run_dir,
    )
    assert summary["route_decision"] == ROUTE_TAIL_WEIGHTED
    assert summary["near_base_alpha_is_exact_zero"] is False
    assert summary["low_tail_rows"] == 120
    assert (run_dir / "alpha_comparison.csv").exists()
    assert (run_dir / "low_tail_rows.csv").exists()
    assert (run_dir / "group_deficit_summary.csv").exists()
