import csv
import json
from pathlib import Path

from autodrift.engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_regression_localization import (
    RESULT_CLASS_PASS,
    run_mitigation_regression_localization,
)


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _behavior_row(
    *,
    row_id: str,
    seed: int,
    axis: str,
    severity: float,
    clearance: float,
    speed: float,
    angle: float,
    margin: float,
    post: bool,
) -> dict[str, object]:
    row: dict[str, object] = {
        "row_id": row_id,
        "scenario_role": "unavoidable_mitigation",
        "seed": seed,
        "subject_id": "m2537_mitigation_preserving_policy",
        "checkpoint_path": "baseline.pt",
        "observation_shape": 72,
        "action_shape": 3,
        "actor_input_leak_flags": "none",
        "collision_event": "True",
        "obstacle_passed_event": "False",
        "road_departure_event": "False",
        "minimum_obstacle_clearance_m": clearance,
        "minimum_road_margin_m": margin,
        "final_road_margin_m": margin,
        "maximum_abs_lateral_velocity": 0.5,
        "maximum_abs_yaw_rate": 0.4,
        "maximum_abs_lateral_position": 0.8,
        "final_abs_lateral_velocity": 0.3,
        "final_abs_yaw_rate": 0.2,
        "recovery_time_proxy_s": 0.02,
        "command_delta_l1_mean": 0.01,
        "simultaneous_throttle_brake_fraction": 0.1,
        "collision_speed_proxy": speed,
        "impact_angle_proxy": angle,
        "severity_proxy": severity,
        "mitigation_delta_against_reference": -0.1,
        "dynamics_axis_id": axis,
    }
    if post:
        row.update(
            {
                "post_repair_row_id": f"m2648_row_{seed}_{axis}",
                "repaired_checkpoint_path": "repaired.pt",
                "protected_reference_family": "mitigation_collision_saturated_reference",
                "protected_reference_only": "True",
                "taxonomy_labels_actor_visible": "False",
                "repair_target_labels_actor_visible": "False",
            }
        )
    return row


def test_mitigation_regression_localization_identifies_penetration_driver(tmp_path):
    baseline_path = tmp_path / "baseline.csv"
    post_path = tmp_path / "post.csv"
    gate_path = tmp_path / "gate.csv"
    summary_path = tmp_path / "m2648_summary.json"
    audit_path = tmp_path / "m2649.md"
    doc_path = tmp_path / "m2650.md"
    follow_up_manifest = tmp_path / "m2651.json"
    output_dir = tmp_path / "run"

    baseline_rows = []
    post_rows = []
    for seed in range(267100, 267104):
        for axis in ("fresh_nominal_or_role_default", "fresh_fault_delay_noise"):
            regressed = seed == 267101 and axis == "fresh_fault_delay_noise"
            baseline_rows.append(
                _behavior_row(
                    row_id=f"baseline_{seed}_{axis}",
                    seed=seed,
                    axis=axis,
                    severity=3.0,
                    clearance=-1.0,
                    speed=3.0,
                    angle=0.4,
                    margin=0.9,
                    post=False,
                )
            )
            post_rows.append(
                _behavior_row(
                    row_id=f"post_{seed}_{axis}",
                    seed=seed,
                    axis=axis,
                    severity=3.1 if regressed else 2.8,
                    clearance=-1.2 if regressed else -0.8,
                    speed=2.9,
                    angle=0.39,
                    margin=1.0,
                    post=True,
                )
            )

    _write_csv(baseline_path, baseline_rows)
    _write_csv(post_path, post_rows)
    _write_csv(
        gate_path,
        [
            {
                "gate_id": "protected_mitigation_reference",
                "gate_pass": "False",
                "failure_type": "behavior_regression",
                "evaluated_row_count": 8,
                "improved_row_count": 7,
                "regressed_row_count": 1,
                "target_or_reference_family": "mitigation_collision_saturated_reference",
            }
        ],
    )
    summary_path.write_text(
        json.dumps(
            {
                "result_class": "engineering_controller_route_a_source_only_gap_targeted_repair_execution_preflight_pass",
                "failed_gate_ids": ["protected_mitigation_reference"],
            }
        ),
        encoding="utf-8",
    )
    audit_path.write_text("M2649 protected mitigation seed 267101 audit", encoding="utf-8")
    follow_up_manifest.write_text("{}", encoding="utf-8")

    summary = run_mitigation_regression_localization(
        output_dir,
        baseline_behavior_rows=baseline_path,
        post_repair_behavior_rows=post_path,
        repair_gate_evaluation=gate_path,
        m2648_summary=summary_path,
        m2649_audit=audit_path,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        milestone="m2650-test",
        next_blocker="m2651-test",
    )

    assert summary["status_pass"] is True
    assert summary["result_class"] == RESULT_CLASS_PASS
    assert summary["matched_protected_mitigation_pair_count"] == 8
    assert summary["mitigation_regression_row_count"] == 1
    assert summary["metric_component_delta_row_count"] == 8 * 15
    assert summary["regressed_seed"] == 267101
    assert summary["regressed_dynamics_axis_id"] == "fresh_fault_delay_noise"
    assert summary["likely_severity_proxy_component_driver"] == "obstacle_penetration_proxy_worsened"
    assert summary["metric_artifact_detected"] is False
    assert summary["real_behavior_regression_localized"] is True
    assert summary["repair_execution_started"] is False
    assert summary["training_run"] is False
    assert summary["success_rate_computed"] is False

    regression_rows = list(csv.DictReader((output_dir / "mitigation_regression_rows.csv").open()))
    assert len(regression_rows) == 1
    assert regression_rows[0]["seed"] == "267101"
    assert regression_rows[0]["likely_severity_proxy_component_driver"] == (
        "obstacle_penetration_proxy_worsened"
    )
    findings = json.loads((output_dir / "localization_findings.json").read_text())
    assert findings["follow_up_manifest_exists"] is True
    assert findings["m2649_audit_mentions_seed_267101"] is True
    assert doc_path.exists()
