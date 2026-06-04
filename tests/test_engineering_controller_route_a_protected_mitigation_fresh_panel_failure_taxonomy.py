import csv
from pathlib import Path

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.engineering_controller_route_a_protected_mitigation_fresh_panel_failure_taxonomy import (
    build_axis_failure_taxonomy_rows,
    build_claim_boundary_rows,
    build_combined_failure_taxonomy_rows,
    build_metric_failure_taxonomy_rows,
    build_subject_failure_taxonomy_rows,
    materialize_failure_taxonomy,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


PANEL_FIELDNAMES = [
    "panel_spec_id",
    "role_class",
    "seed",
    "dynamics_axis_id",
    "dynamics_axis_family",
]
BEHAVIOR_FIELDNAMES = [
    "scenario_role",
    "seed",
    "subject_id",
    "observation_shape",
    "action_shape",
    "actor_input_leak_flags",
    "protected_rows_in_success_denominator",
]
GATE_FIELDNAMES = [
    "gate_id",
    "gate_family",
    "subject_id",
    "dynamics_axis_id",
    "metric",
    "metric_direction",
    "evaluated_row_count",
    "reference_subject_id",
    "reference_mean",
    "subject_mean",
    "improved_row_count",
    "regressed_row_count",
    "unchanged_row_count",
    "gate_pass",
    "blocks_claims",
    "failure_type",
    "interpretation",
    "claim_scope",
]


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _gate_row(subject, axis, metric, *, blocks=True, regressed=4, improved=0):
    return {
        "gate_id": f"gate_{subject}_{axis}_{metric}",
        "gate_family": "protected_mitigation_reference_comparison",
        "subject_id": subject,
        "dynamics_axis_id": axis,
        "metric": metric,
        "metric_direction": "lower_is_better",
        "evaluated_row_count": 4,
        "reference_subject_id": "straight_full_brake_open_loop",
        "reference_mean": 1.0,
        "subject_mean": 2.0 if blocks else 0.8,
        "improved_row_count": improved,
        "regressed_row_count": regressed,
        "unchanged_row_count": 0,
        "gate_pass": not blocks,
        "blocks_claims": blocks,
        "failure_type": "behavior_regression" if blocks else "",
        "interpretation": "diagnostic protected mitigation blocker row",
        "claim_scope": "test",
    }


def _sample_gate_rows():
    rows = []
    blocking_idx = 0
    subjects = (
        "m1154_original_policy",
        "m2532_guarded_repair_policy",
        "m2537_mitigation_preserving_policy",
    )
    axes = (
        "fresh_protected_nominal",
        "fresh_protected_fault_delay_noise",
        "fresh_protected_close_cut_in_fault",
    )
    metrics = (
        "severity_proxy",
        "obstacle_penetration_proxy_m",
        "minimum_obstacle_clearance_m",
    )
    for subject in subjects:
        for axis in axes:
            for metric in metrics:
                blocks = not (
                    subject != "m1154_original_policy"
                    and axis == "fresh_protected_nominal"
                    and metric == "severity_proxy"
                )
                regressed = 0
                if blocks:
                    blocking_idx += 1
                    regressed = 4 if blocking_idx <= 4 else 3
                rows.append(_gate_row(subject, axis, metric, blocks=blocks, regressed=regressed))
    return rows


def test_taxonomy_builders_preserve_protected_blocker_shape():
    gate_rows = _sample_gate_rows()
    seeds = ["268200", "268201", "268202", "268203"]
    panel_rows = [
        {
            "dynamics_axis_id": "fresh_protected_nominal",
            "dynamics_axis_family": "protected_nominal",
        },
        {
            "dynamics_axis_id": "fresh_protected_fault_delay_noise",
            "dynamics_axis_family": "protected_fault_delay_noise",
        },
        {
            "dynamics_axis_id": "fresh_protected_close_cut_in_fault",
            "dynamics_axis_family": "protected_close_cut_in_fault",
        },
    ]

    subject_rows = build_subject_failure_taxonomy_rows(gate_rows, seed_ids=seeds)
    axis_rows = build_axis_failure_taxonomy_rows(gate_rows, panel_rows=panel_rows, seed_ids=seeds)
    metric_rows = build_metric_failure_taxonomy_rows(gate_rows, seed_ids=seeds)
    combined_rows = build_combined_failure_taxonomy_rows(gate_rows, seed_ids=seeds)
    claim_rows = build_claim_boundary_rows()

    assert len(subject_rows) == 3
    assert len(axis_rows) == 3
    assert len(metric_rows) == 3
    assert len(combined_rows) == 9
    assert sum(int(row["blocking_gate_row_count"]) for row in subject_rows) == 25
    assert {row["actor_visible_allowed"] for row in subject_rows + axis_rows + metric_rows} == {False}
    assert {row["protected_rows_in_success_denominator"] for row in combined_rows} == {False}
    assert {row["allowed_in_m2664"] for row in claim_rows if row["claim_family"] == "driver_performance"} == {
        False
    }


def test_materialize_failure_taxonomy_writes_expected_artifacts(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2664.md"
    follow_up = tmp_path / "m2665.json"
    follow_up.write_text("{}\n", encoding="utf-8")
    summary_path = tmp_path / "summary.json"
    panel_path = tmp_path / "panel.csv"
    behavior_path = tmp_path / "behavior.csv"
    gates_path = tmp_path / "protected_gates.csv"
    claim_path = tmp_path / "claims.csv"
    gate_matrix_path = tmp_path / "gate_matrix.csv"

    seeds = ["268200", "268201", "268202", "268203"]
    axes = [
        ("fresh_protected_nominal", "protected_nominal"),
        ("fresh_protected_fault_delay_noise", "protected_fault_delay_noise"),
        ("fresh_protected_close_cut_in_fault", "protected_close_cut_in_fault"),
    ]
    panel_rows = [
        {
            "panel_spec_id": f"panel_{seed}_{axis}",
            "role_class": "protected",
            "seed": seed,
            "dynamics_axis_id": axis,
            "dynamics_axis_family": family,
        }
        for seed in seeds
        for axis, family in axes
    ]
    behavior_rows = [
        {
            "scenario_role": "unavoidable_mitigation",
            "seed": seed,
            "subject_id": subject,
            "observation_shape": P0_OBSERVATION_DIM,
            "action_shape": ACTION_DIM,
            "actor_input_leak_flags": "none",
            "protected_rows_in_success_denominator": False,
        }
        for seed in seeds
        for subject in [
            "m1154_original_policy",
            "m2532_guarded_repair_policy",
            "m2537_mitigation_preserving_policy",
            "coast_open_loop",
            "straight_full_brake_open_loop",
        ]
        for _axis, _family in axes
    ]
    gate_rows = _sample_gate_rows()
    write_json(
        summary_path,
        {
            "status_pass": True,
            "target_protected_split_preserved": True,
            "hidden_oracle_actor_input_detected": False,
        },
    )
    write_csv_rows(panel_path, panel_rows, fieldnames=PANEL_FIELDNAMES)
    write_csv_rows(behavior_path, behavior_rows, fieldnames=BEHAVIOR_FIELDNAMES)
    write_csv_rows(gates_path, gate_rows, fieldnames=GATE_FIELDNAMES)
    write_csv_rows(
        claim_path,
        [{"claim_id": "allowed", "status_pass": True}],
        fieldnames=["claim_id", "status_pass"],
    )
    write_csv_rows(
        gate_matrix_path,
        [{"gate_id": "source", "status_pass": True}],
        fieldnames=["gate_id", "status_pass"],
    )

    summary = materialize_failure_taxonomy(
        output_dir,
        summary_path=summary_path,
        panel_spec_rows_path=panel_path,
        measured_behavior_rows_path=behavior_path,
        protected_mitigation_gates_path=gates_path,
        claim_boundary_rows_path=claim_path,
        gate_matrix_path=gate_matrix_path,
        follow_up_manifest=follow_up,
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert summary["subject_failure_taxonomy_row_count"] == 3
    assert summary["axis_failure_taxonomy_row_count"] == 3
    assert summary["metric_failure_taxonomy_row_count"] == 3
    assert summary["combined_failure_taxonomy_row_count"] == 9
    assert summary["protected_gate_blocking_row_count"] == 25
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["taxonomy_labels_actor_visible"] is False
    assert summary["driver_performance_claim_made"] is False

    assert len(_read_csv(output_dir / "subject_failure_taxonomy_rows.csv")) == 3
    assert len(_read_csv(output_dir / "axis_failure_taxonomy_rows.csv")) == 3
    assert len(_read_csv(output_dir / "metric_failure_taxonomy_rows.csv")) == 3
    assert len(_read_csv(output_dir / "combined_failure_taxonomy_rows.csv")) == 9
    assert len(_read_csv(output_dir / "claim_boundary_rows.csv")) == 16
    assert doc_path.exists()
