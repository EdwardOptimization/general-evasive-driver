import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.engineering_controller_route_a_source_only_behavior_gap_taxonomy import (
    build_claim_boundary_rows,
    build_dynamics_axis_gap_rows,
    build_repair_target_admission_rows,
    build_role_gap_rows,
    build_subject_gap_rows,
    materialize_behavior_gap_taxonomy,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


FIELDNAMES = [
    "scenario_role",
    "subject_id",
    "seed",
    "dynamics_axis_id",
    "observation_shape",
    "action_shape",
    "diagnostic_only_no_ranking_claim",
    "collision_event",
    "road_departure_event",
    "obstacle_passed_event",
    "minimum_obstacle_clearance_m",
    "minimum_road_margin_m",
    "maximum_abs_lateral_position",
    "severity_proxy",
]


def _row(role, subject, axis, *, seed, collision=False, road=False, clearance=2.0, margin=1.0):
    return {
        "scenario_role": role,
        "subject_id": subject,
        "seed": seed,
        "dynamics_axis_id": axis,
        "observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "diagnostic_only_no_ranking_claim": True,
        "collision_event": collision,
        "road_departure_event": road,
        "obstacle_passed_event": False,
        "minimum_obstacle_clearance_m": clearance,
        "minimum_road_margin_m": margin,
        "maximum_abs_lateral_position": abs(margin),
        "severity_proxy": 5.0 if collision else 0.0,
    }


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _sample_rows():
    subjects = ("policy_a", "reference_b")
    axes = ("fresh_nominal_or_role_default", "fresh_fault_delay_noise")
    rows = []
    for subject in subjects:
        for axis in axes:
            rows.append(_row("stable_avoidable", subject, axis, seed=1, road=True, margin=-0.5))
            rows.append(_row("stable_aes", subject, axis, seed=2, road=True, margin=-1.0))
            rows.append(
                _row(
                    "drift_required_recovery",
                    subject,
                    axis,
                    seed=3,
                    collision=subject == "reference_b",
                    road=True,
                    clearance=-0.4 if subject == "reference_b" else 1.2,
                    margin=-1.5,
                )
            )
            rows.append(
                _row(
                    "unavoidable_mitigation",
                    subject,
                    axis,
                    seed=4,
                    collision=True,
                    clearance=-0.8,
                    margin=0.5,
                )
            )
    return rows


def test_gap_builders_classify_expected_gap_families():
    rows = _sample_rows()
    role_rows = build_role_gap_rows(rows)
    subject_rows = build_subject_gap_rows(rows)
    axis_rows = build_dynamics_axis_gap_rows(rows)
    repair_rows = build_repair_target_admission_rows(role_rows, axis_rows)
    claim_rows = build_claim_boundary_rows()

    by_role = {row["scenario_role"]: row for row in role_rows}
    assert by_role["stable_avoidable"]["primary_gap_family"] == "road_departure_dominant_gap"
    assert by_role["stable_aes"]["primary_gap_family"] == "road_departure_dominant_gap"
    assert by_role["drift_required_recovery"]["primary_gap_family"] == "drift_recovery_mixed_gap"
    assert (
        by_role["unavoidable_mitigation"]["primary_gap_family"]
        == "mitigation_collision_saturated_reference"
    )
    assert len(subject_rows) == 8
    assert len(axis_rows) == 8
    assert {row["axis_sensitivity_interpretation"] for row in axis_rows} == {
        "axis_sensitivity_not_yet_decisive"
    }
    repair_by_gap = {row["gap_family"]: row for row in repair_rows}
    assert repair_by_gap["road_departure_dominant_gap"]["admitted_for_repair_design"] is True
    assert repair_by_gap["drift_recovery_mixed_gap"]["admitted_for_repair_design"] is True
    assert repair_by_gap["mitigation_collision_saturated_reference"]["reference_only"] is True
    assert repair_by_gap["axis_sensitivity_not_yet_decisive"]["admitted_for_repair_design"] is False
    assert repair_by_gap["axis_sensitivity_not_yet_decisive"]["reference_only"] is True
    assert {row["allowed_in_m2644"] for row in claim_rows if row["claim_family"] == "driver_performance"} == {
        False
    }


def test_materialize_behavior_gap_taxonomy_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2644.md"
    next_manifest = tmp_path / "m2645.json"
    next_manifest.write_text("{}\n", encoding="utf-8")
    behavior_path = tmp_path / "measured_behavior_rows.csv"
    event_path = tmp_path / "measured_event_rows.csv"
    telemetry_path = tmp_path / "telemetry_rows.csv"
    gate_path = tmp_path / "gate_matrix.csv"
    guard_path = tmp_path / "actor_visibility_guard_rows.csv"
    summary_path = tmp_path / "summary.json"
    audit_doc = tmp_path / "m2642.md"
    synthesis_doc = tmp_path / "m2643.md"
    audit_doc.write_text("audit\n", encoding="utf-8")
    synthesis_doc.write_text("synthesis\n", encoding="utf-8")

    rows = _sample_rows()
    write_csv_rows(behavior_path, rows, fieldnames=FIELDNAMES)
    write_csv_rows(event_path, rows, fieldnames=FIELDNAMES)
    write_csv_rows(telemetry_path, rows, fieldnames=FIELDNAMES)
    write_csv_rows(gate_path, [{"status_pass": True}], fieldnames=["status_pass"])
    write_csv_rows(guard_path, [{"status_pass": True}], fieldnames=["status_pass"])
    write_json(summary_path, {"status_pass": True})

    summary = materialize_behavior_gap_taxonomy(
        output_dir,
        measured_behavior_rows_path=behavior_path,
        measured_event_rows_path=event_path,
        telemetry_rows_path=telemetry_path,
        summary_path=summary_path,
        gate_matrix_path=gate_path,
        actor_guard_path=guard_path,
        audit_doc_path=audit_doc,
        synthesis_doc_path=synthesis_doc,
        next_manifest_path=next_manifest,
        doc_path=doc_path,
    )

    assert summary["status_pass"] is False
    assert summary["role_gap_row_count"] == 4
    assert summary["subject_gap_row_count"] == 8
    assert summary["dynamics_axis_gap_row_count"] == 8
    assert summary["repair_target_admission_row_count"] == 4
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["taxonomy_labels_actor_visible"] is False
    assert summary["repair_targets_available_for_audit"] is True
    assert summary["next_audit_manifest_registered"] is True
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False

    assert len(_read_csv(output_dir / "role_gap_rows.csv")) == 4
    assert len(_read_csv(output_dir / "subject_gap_rows.csv")) == 8
    assert len(_read_csv(output_dir / "dynamics_axis_gap_rows.csv")) == 8
    assert len(_read_csv(output_dir / "repair_target_admission_rows.csv")) == 4
    assert len(_read_csv(output_dir / "claim_boundary_rows.csv")) == 13
    assert doc_path.exists()
