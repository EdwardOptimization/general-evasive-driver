import csv

import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel import (
    PROTECTED_DYNAMICS_AXES,
    PROTECTED_ROLE,
    build_protected_mitigation_gate_rows,
    build_protected_mitigation_panel_specs,
    materialize_protected_mitigation_fresh_failure_surface_panel,
)
from autodrift.engineering_controller_route_a_source_only_execution_readiness_panel import (
    POLICY_SUBJECT_IDS,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.train_ppo import ActorCritic


EVIDENCE_FIELDNAMES = [
    "evidence_id",
    "source_milestone",
    "artifact_path",
    "evidence_family",
    "evidence_role",
    "evidence_status",
    "row_count",
    "target_or_protected",
    "target_improvement_evidence",
    "protected_failure_blocking",
    "actor_contract_shape_72_action_3",
    "hidden_oracle_actor_input_detected",
    "source_exists",
    "next_use",
    "claim_scope",
    "forbidden_interpretation",
]
GAP_FIELDNAMES = [
    "gap_id",
    "route",
    "evidence_family",
    "current_status",
    "blocker",
    "required_next_evidence",
    "admission_to_next_action",
    "evidence_expansion_value",
    "forbidden_shortcut",
    "claim_scope",
]
TRADEOFF_FIELDNAMES = [
    "tradeoff_id",
    "source_stage",
    "gate_id",
    "gate_family",
    "target_or_reference_family",
    "scenario_role_group",
    "role_class",
    "metric",
    "evaluated_row_count",
    "improved_row_count",
    "regressed_row_count",
    "unchanged_row_count",
    "gate_pass",
    "failure_type",
    "failed_gate_ids",
    "target_preservation_gates_all_passed",
    "protected_component_gates_all_passed",
    "target_and_protected_gates_all_passed",
    "selected_candidate_id",
    "selected_candidate_treated_as_winner",
    "protected_rows_in_success_denominator",
    "blocks_claims",
    "interpretation",
    "claim_scope",
]
FOCUS_FIELDNAMES = [
    "focus_id",
    "subject_id",
    "scenario_role",
    "seed",
    "dynamics_axis_id",
    "baseline_severity_proxy",
    "m2648_severity_proxy",
    "m2655_severity_proxy",
    "m2648_severity_delta",
    "m2655_severity_delta",
    "baseline_obstacle_penetration_proxy_m",
    "m2648_obstacle_penetration_proxy_m",
    "m2655_obstacle_penetration_proxy_m",
    "m2648_obstacle_penetration_delta",
    "m2655_obstacle_penetration_delta",
    "baseline_minimum_obstacle_clearance_m",
    "m2648_minimum_obstacle_clearance_m",
    "m2655_minimum_obstacle_clearance_m",
    "m2648_clearance_delta",
    "m2655_clearance_delta",
    "m2648_any_protected_component_regressed",
    "m2655_any_protected_component_regressed",
    "m2650_regressed_row_match",
    "blocks_claims",
    "claim_scope",
]


def _model_config(**overrides):
    config = {
        "device": "cpu",
        "actor_encoder": "human_view_online_gru",
        "actor_history_length": 1,
        "action_sequence_horizon": 1,
        "response_prediction_dim": 0,
        "response_prediction_horizon": 1,
        "log_std_init": -1.0,
        "log_std_min": -5.0,
        "log_std_max": -0.5,
    }
    config.update(overrides)
    return config


def _write_checkpoint(path):
    model = ActorCritic(
        obs_dim=P0_OBSERVATION_DIM,
        act_dim=ACTION_DIM,
        hidden_size=16,
        actor_encoder="human_view_online_gru",
        action_sequence_horizon=1,
    )
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": _model_config(),
        },
        path,
    )


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _source_paths(tmp_path):
    evidence_index = tmp_path / "evidence_index.csv"
    gap_matrix = tmp_path / "gap_matrix.csv"
    tradeoff = tmp_path / "target_protected.csv"
    focus = tmp_path / "focus.csv"
    follow_up = tmp_path / "m2663.json"
    follow_up.write_text("{}\n", encoding="utf-8")
    write_csv_rows(
        evidence_index,
        [
            {
                "evidence_id": "m2657_protected_tradeoff_rows",
                "source_milestone": "m2657",
                "artifact_path": "m2657.csv",
                "evidence_family": "protected_tradeoff_rows",
                "evidence_role": "protected_failure_blocker",
                "evidence_status": "materialized_blocking",
                "row_count": 5,
                "target_or_protected": "protected",
                "target_improvement_evidence": False,
                "protected_failure_blocking": True,
                "actor_contract_shape_72_action_3": True,
                "hidden_oracle_actor_input_detected": False,
                "source_exists": True,
                "next_use": "panel",
                "claim_scope": "test",
                "forbidden_interpretation": "test",
            }
        ],
        fieldnames=EVIDENCE_FIELDNAMES,
    )
    write_csv_rows(
        gap_matrix,
        [
            {
                "gap_id": "route_a_protected_mitigation_blocker",
                "route": "Route A",
                "evidence_family": "protected_tradeoff_rows",
                "current_status": "blocking",
                "blocker": "protected mitigation",
                "required_next_evidence": "fresh panel",
                "admission_to_next_action": "admitted",
                "evidence_expansion_value": "fresh panel",
                "forbidden_shortcut": "do not weaken gates",
                "claim_scope": "test",
            }
        ],
        fieldnames=GAP_FIELDNAMES,
    )
    write_csv_rows(
        tradeoff,
        [
            {
                "tradeoff_id": "protected",
                "source_stage": "m2655",
                "gate_id": "severity_proxy_non_regression",
                "gate_family": "protected_component",
                "target_or_reference_family": "mitigation",
                "scenario_role_group": PROTECTED_ROLE,
                "role_class": "protected",
                "metric": "severity_proxy",
                "evaluated_row_count": 8,
                "improved_row_count": 7,
                "regressed_row_count": 1,
                "unchanged_row_count": 0,
                "gate_pass": False,
                "failure_type": "behavior_regression",
                "failed_gate_ids": "severity_proxy_non_regression",
                "target_preservation_gates_all_passed": True,
                "protected_component_gates_all_passed": False,
                "target_and_protected_gates_all_passed": False,
                "selected_candidate_id": "m2655_softened_gap_bias",
                "selected_candidate_treated_as_winner": False,
                "protected_rows_in_success_denominator": False,
                "blocks_claims": True,
                "interpretation": "blocking",
                "claim_scope": "test",
            }
        ],
        fieldnames=TRADEOFF_FIELDNAMES,
    )
    write_csv_rows(
        focus,
        [
            {
                "focus_id": f"focus_{idx}",
                "subject_id": "m2537_mitigation_preserving_policy",
                "scenario_role": PROTECTED_ROLE,
                "seed": 267100 + idx,
                "dynamics_axis_id": "fresh_fault_delay_noise",
                "baseline_severity_proxy": 1.0,
                "m2648_severity_proxy": 1.1,
                "m2655_severity_proxy": 1.08,
                "m2648_severity_delta": 0.1,
                "m2655_severity_delta": 0.08,
                "baseline_obstacle_penetration_proxy_m": 0.5,
                "m2648_obstacle_penetration_proxy_m": 0.6,
                "m2655_obstacle_penetration_proxy_m": 0.58,
                "m2648_obstacle_penetration_delta": 0.1,
                "m2655_obstacle_penetration_delta": 0.08,
                "baseline_minimum_obstacle_clearance_m": -0.5,
                "m2648_minimum_obstacle_clearance_m": -0.6,
                "m2655_minimum_obstacle_clearance_m": -0.58,
                "m2648_clearance_delta": -0.1,
                "m2655_clearance_delta": -0.08,
                "m2648_any_protected_component_regressed": True,
                "m2655_any_protected_component_regressed": True,
                "m2650_regressed_row_match": idx == 0,
                "blocks_claims": True,
                "claim_scope": "test",
            }
            for idx in range(4)
        ],
        fieldnames=FOCUS_FIELDNAMES,
    )
    write_json(
        tmp_path / "m2659_summary.json",
        {
            "status_pass": True,
            "target_protected_split_preserved": True,
            "protected_failure_blocking": True,
        },
    )
    write_json(
        tmp_path / "m2657_summary.json",
        {
            "status_pass": True,
            "m2655_target_preservation_gates_all_passed": True,
            "m2655_protected_component_gates_all_passed": False,
        },
    )
    return evidence_index, gap_matrix, tradeoff, focus, follow_up


def test_protected_panel_specs_use_fresh_protected_seeds_and_axes():
    focus_rows = [
        {"seed": str(267100 + idx), "dynamics_axis_id": "fresh_fault_delay_noise"}
        for idx in range(4)
    ]
    run_items, panel_rows = build_protected_mitigation_panel_specs(
        focus_rows,
        protected_seed_count=2,
    )

    assert len(run_items) == 2 * len(PROTECTED_DYNAMICS_AXES)
    assert len(panel_rows) == len(run_items)
    assert {row["role_family"] for row in panel_rows} == {PROTECTED_ROLE}
    assert {row["dynamics_axis_id"] for row in panel_rows} == set(PROTECTED_DYNAMICS_AXES)
    assert {row["fresh_seed_not_in_m2641"] for row in panel_rows} == {True}
    assert any(row["fresh_failure_surface_axis"] for row in panel_rows)
    assert {row["actor_visible_allowed"] for row in panel_rows} == {False}


def test_protected_gate_rows_keep_blocking_rows_outside_success_claims():
    rows = []
    for seed in [1, 2]:
        rows.append(
            {
                "subject_id": "m2537_mitigation_preserving_policy",
                "seed": seed,
                "dynamics_axis_id": "axis",
                "severity_proxy": 2.0 + seed,
                "minimum_obstacle_clearance_m": -1.0 - seed,
            }
        )
        rows.append(
            {
                "subject_id": "straight_full_brake_open_loop",
                "seed": seed,
                "dynamics_axis_id": "axis",
                "severity_proxy": 1.0,
                "minimum_obstacle_clearance_m": -0.5,
            }
        )

    gate_rows = build_protected_mitigation_gate_rows(rows)

    assert gate_rows
    assert any(row["blocks_claims"] for row in gate_rows)
    assert any(row["failure_type"] == "behavior_regression" for row in gate_rows)
    assert {row["claim_scope"] for row in gate_rows}


def test_materialize_protected_mitigation_panel_writes_required_artifacts(tmp_path, monkeypatch):
    checkpoints = {}
    for subject_id in POLICY_SUBJECT_IDS:
        checkpoint = tmp_path / f"{subject_id}.pt"
        _write_checkpoint(checkpoint)
        checkpoints[subject_id] = checkpoint
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2662.md"
    evidence_index, gap_matrix, tradeoff, focus, follow_up = _source_paths(tmp_path)
    monkeypatch.setattr(
        "autodrift.engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel.DEFAULT_M2659_SUMMARY",
        tmp_path / "m2659_summary.json",
    )
    monkeypatch.setattr(
        "autodrift.engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel.DEFAULT_M2657_SUMMARY",
        tmp_path / "m2657_summary.json",
    )
    monkeypatch.setattr(
        "autodrift.engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel.M2661_DOC",
        follow_up,
    )

    summary = materialize_protected_mitigation_fresh_failure_surface_panel(
        output_dir,
        evidence_index=evidence_index,
        gap_matrix=gap_matrix,
        target_protected_report=tradeoff,
        protected_focus_rows=focus,
        follow_up_manifest=follow_up,
        doc_path=doc_path,
        protected_seed_count=2,
        horizon_steps=1,
        policy_checkpoints=checkpoints,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_protected_mitigation_fresh_failure_surface_panel_materialization_preflight_pass"
    )
    assert summary["source_evidence_consumed_as_design_input_only"] is True
    assert summary["protected_role"] == PROTECTED_ROLE
    assert summary["fresh_protected_seed_count"] == 2
    assert summary["dynamics_axis_count"] == len(PROTECTED_DYNAMICS_AXES)
    assert summary["panel_spec_row_count"] == 6
    assert summary["measured_behavior_row_count"] == 30
    assert summary["protected_mitigation_gate_row_count"] == 27
    assert summary["target_protected_split_preserved"] is True
    assert summary["protected_blocker_source_preserved"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["follow_up_manifest_registered"] is True

    panel_rows = _read_csv(output_dir / "panel_spec_rows.csv")
    behavior_rows = _read_csv(output_dir / "measured_behavior_rows.csv")
    gate_rows = _read_csv(output_dir / "protected_mitigation_gate_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    matrix_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert len(panel_rows) == 6
    assert len(behavior_rows) == 30
    assert len(gate_rows) == 27
    assert {row["scenario_role"] for row in behavior_rows} == {PROTECTED_ROLE}
    assert {row["observation_shape"] for row in behavior_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in behavior_rows} == {str(ACTION_DIM)}
    assert {row["protected_rows_in_success_denominator"] for row in behavior_rows} == {"False"}
    assert {row["actor_visible_labels"] for row in behavior_rows} == {"False"}
    assert {row["status_pass"] for row in claim_rows} == {"True"}
    assert {row["status_pass"] for row in matrix_rows} == {"True"}
    assert doc_path.exists()
