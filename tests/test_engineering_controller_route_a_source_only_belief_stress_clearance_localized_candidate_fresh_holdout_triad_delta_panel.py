import csv
import json
from pathlib import Path

import torch

from autodrift.engineering_controller_failure_surface_guarded_repair_execution import _file_sha256
from autodrift.engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel import (
    DEFAULT_NEXT_BLOCKER,
    run_clearance_localized_candidate_fresh_holdout_triad_delta_panel,
)
from autodrift.engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight import (
    DYNAMICS_AXES,
    ORDINARY_ROLE_FAMILIES,
    STRESS_FAMILIES,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM
from autodrift.train_ppo import ActorCritic


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


def _write_checkpoint(path: Path, *, bias_delta: float = 0.0):
    model = ActorCritic(
        obs_dim=P0_OBSERVATION_DIM,
        act_dim=ACTION_DIM,
        hidden_size=16,
        actor_encoder="human_view_online_gru",
        action_sequence_horizon=1,
    )
    with torch.no_grad():
        model.actor_mean.bias[0].add_(bias_delta)
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": _model_config(),
        },
        path,
    )


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _objective_rows():
    rows = []
    index = 0
    for role in ORDINARY_ROLE_FAMILIES:
        for axis in DYNAMICS_AXES:
            for stress in STRESS_FAMILIES:
                objective_family = (
                    "stable_avoidable_retention"
                    if role == "stable_avoidable"
                    else "target_clearance_correction"
                )
                rows.append(
                    {
                        "training_objective_row_id": f"m2799_objective_{index:03d}",
                        "objective_family": objective_family,
                        "source_aggregate_id": f"agg_{index:03d}",
                        "source_curriculum_row_id": f"source_{role}_{axis}_{stress}",
                        "role_family": role,
                        "dynamics_axis": axis,
                        "stress_family": stress,
                        "future_training_allowed": objective_family == "target_clearance_correction",
                        "future_execution_allowed": True,
                        "actor_visible_label": False,
                        "ordinary_denominator_allowed": True,
                        "ranking_admissible": False,
                        "obstacle_clearance_guard_required": True,
                        "clearance_hard_before_side_effects": True,
                        "claim_boundary": "test",
                    }
                )
                index += 1
    return rows


def _write_m2799_sources(path: Path, source: Path, start: Path, candidate: Path, m2782_hash: str):
    path.mkdir(parents=True, exist_ok=True)
    source_hash = _file_sha256(source)
    start_hash = _file_sha256(start)
    candidate_hash = _file_sha256(candidate)
    (path / "summary.json").write_text(
        json.dumps(
            {
                "status_pass": True,
                "required_artifacts_present": True,
                "gate_matrix_pass": True,
                "source_reference_checkpoint_hash": source_hash,
                "base_candidate_checkpoint_hash": m2782_hash,
                "start_candidate_checkpoint_hash": start_hash,
                "candidate_checkpoint_hash": candidate_hash,
            }
        ),
        encoding="utf-8",
    )
    (path / "checkpoint_manifest.json").write_text(
        json.dumps(
            {
                "source_reference_checkpoint_hash": source_hash,
                "base_candidate_checkpoint_hash": m2782_hash,
                "start_candidate_checkpoint_hash": start_hash,
                "candidate_checkpoint_hash": candidate_hash,
                "candidate_checkpoint_written": True,
                "checkpoint_promoted": False,
            }
        ),
        encoding="utf-8",
    )
    _write_rows(path / "training_objective_rows.csv", _objective_rows())
    _write_rows(
        path / "mitigation_reference_guard_rows.csv",
        [
            {
                "source_guard_id": "mitigation_a",
                "candidate_id": "mitigation_a",
                "role_family": "unavoidable_mitigation",
                "dynamics_axis": "fresh_fault_delay_noise",
                "seed": 267100,
                "mitigation_reference": True,
                "ordinary_denominator_allowed": False,
                "future_training_allowed": False,
                "future_execution_allowed": False,
            }
        ],
    )
    (path / "gate_matrix.csv").write_text("gate_id,status_pass\nm2799_gate,True\n", encoding="utf-8")
    (path / "behavior_retention_gate_rows.csv").write_text(
        "gate_id,status_pass\nbehavior_guard,True\n",
        encoding="utf-8",
    )


def _write_m2796_sources(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "summary.json").write_text(
        json.dumps({"status_pass": True, "gate_matrix_pass": True}),
        encoding="utf-8",
    )
    _write_rows(
        path / "clearance_regression_aggregate_rows.csv",
        [
            {
                "aggregate_id": "drift_role",
                "group_family": "role_family",
                "role_family": "drift_required_recovery",
                "row_count": 48,
                "negative_clearance_count": 48,
            },
            {
                "aggregate_id": "aes_role",
                "group_family": "role_family",
                "role_family": "stable_aes",
                "row_count": 48,
                "negative_clearance_count": 36,
            },
            {
                "aggregate_id": "stable_role",
                "group_family": "role_family",
                "role_family": "stable_avoidable",
                "row_count": 48,
                "negative_clearance_count": 1,
            },
        ],
    )


def _write_m2793_sources(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "summary.json").write_text(
        json.dumps(
            {
                "status_pass": True,
                "horizon_steps": 140,
                "fresh_holdout_seed_indices": [8, 9, 10, 11],
            }
        ),
        encoding="utf-8",
    )
    previous_rows = [
        {"pair_id": f"p{seed}", "seed_index": seed}
        for seed in (8, 9, 10, 11)
    ]
    _write_rows(path / "candidate_minus_source_delta_rows.csv", previous_rows)
    _write_rows(path / "candidate_minus_base_delta_rows.csv", previous_rows)


def test_m2801_clearance_localized_candidate_fresh_holdout_triad_panel_writes_claim_safe_deltas(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2801.md"
    follow_up_manifest = tmp_path / "m2802.json"
    m2800_audit = tmp_path / "m2800.md"
    m2799_dir = tmp_path / "m2799"
    m2796_dir = tmp_path / "m2796"
    m2793_dir = tmp_path / "m2793"
    source_checkpoint = tmp_path / "source.pt"
    start_checkpoint = tmp_path / "start.pt"
    candidate_checkpoint = tmp_path / "candidate.pt"
    m2800_audit.write_text("# audit\n", encoding="utf-8")
    _write_checkpoint(source_checkpoint, bias_delta=0.0)
    _write_checkpoint(start_checkpoint, bias_delta=0.03)
    _write_checkpoint(candidate_checkpoint, bias_delta=0.04)
    _write_m2799_sources(
        m2799_dir,
        source_checkpoint,
        start_checkpoint,
        candidate_checkpoint,
        "m2782_base_hash",
    )
    _write_m2796_sources(m2796_dir)
    _write_m2793_sources(m2793_dir)

    summary = run_clearance_localized_candidate_fresh_holdout_triad_delta_panel(
        output_dir,
        m2800_audit=m2800_audit,
        m2799_dir=m2799_dir,
        m2796_dir=m2796_dir,
        m2793_dir=m2793_dir,
        source_checkpoint=source_checkpoint,
        base_candidate_checkpoint=start_checkpoint,
        candidate_checkpoint=candidate_checkpoint,
        follow_up_manifest=follow_up_manifest,
        doc_path=doc_path,
        device="cpu",
        seed_start_index=12,
        seed_count=2,
        horizon_steps=160,
        milestone="m2801-test",
        next_blocker="m2802-test",
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_source_only_belief_stress_clearance_localized_candidate_fresh_holdout_triad_delta_panel_preflight_pass"
    )
    assert summary["m2799_status_pass"] is True
    assert summary["m2796_status_pass"] is True
    assert summary["seed_start_index"] == 12
    assert summary["seed_count"] == 2
    assert summary["fresh_holdout_seed_indices"] == [12, 13]
    assert summary["fresh_holdout_seed_indices_disjoint_from_previous"] is True
    assert summary["horizon_longer_than_m2793"] is True
    assert summary["objective_row_count"] == 18
    assert summary["triad_execution_row_count"] == 108
    assert summary["candidate_minus_source_delta_row_count"] == 36
    assert summary["candidate_minus_base_delta_row_count"] == 36
    assert summary["proof_gate_row_count"] == 16
    assert summary["generalization_gate_row_count"] == 9
    assert summary["behavior_retention_gate_row_count"] == 9
    assert summary["promotion_guard_row_count"] == 4
    assert summary["gate_matrix_row_count"] == 38
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["actor_visible_atlas_or_role_labels_detected"] is False
    assert summary["mitigation_reference_rows_guarded"] is True
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["repair_success_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["m2802_follow_up_manifest_registered"] is True

    execution_rows = _read_csv(output_dir / "triad_execution_rows.csv")
    source_delta_rows = _read_csv(output_dir / "candidate_minus_source_delta_rows.csv")
    base_delta_rows = _read_csv(output_dir / "candidate_minus_base_delta_rows.csv")
    mitigation_rows = _read_csv(output_dir / "mitigation_reference_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    m2802 = json.loads(follow_up_manifest.read_text())

    assert len(execution_rows) == 108
    assert len(source_delta_rows) == 36
    assert len(base_delta_rows) == 36
    assert len(gate_rows) == 38
    assert {row["checkpoint_subject"] for row in execution_rows} == {"source", "base_candidate", "candidate"}
    assert {row["seed_index"] for row in execution_rows} == {"12", "13"}
    assert {row["delta_family"] for row in source_delta_rows} == {"candidate_minus_source"}
    assert {row["delta_family"] for row in base_delta_rows} == {"candidate_minus_base"}
    assert {row["observation_shape"] for row in execution_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in execution_rows} == {str(ACTION_DIM)}
    assert {row["actor_visible_label"] for row in execution_rows} == {"False"}
    assert {row["hidden_or_oracle_actor_inputs_required"] for row in execution_rows} == {"False"}
    assert {row["diagnostic_only"] for row in source_delta_rows + base_delta_rows} == {"True"}
    assert {row["ranking_admissible"] for row in source_delta_rows + base_delta_rows} == {"False"}
    assert {row["winner_selected"] for row in source_delta_rows + base_delta_rows} == {"False"}
    assert {row["success_rate_verdict_computed"] for row in source_delta_rows + base_delta_rows} == {"False"}
    assert {row["ordinary_denominator_allowed"] for row in mitigation_rows} == {"False"}
    assert {row["included_in_paired_execution_rows"] for row in mitigation_rows} == {"False"}
    assert {
        row["claim_id"]: row["claim_made"]
        for row in claim_rows
        if row["claim_id"] in {"validation_result", "ranking_result", "checkpoint_promotion"}
    } == {
        "validation_result": "False",
        "ranking_result": "False",
        "checkpoint_promotion": "False",
    }
    assert m2802["id"] == DEFAULT_NEXT_BLOCKER
    assert m2802["training_stage"]["stage"] == "process"
    assert doc_path.exists()
