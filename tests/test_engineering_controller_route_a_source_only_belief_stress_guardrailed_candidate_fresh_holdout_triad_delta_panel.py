import csv
import json
from pathlib import Path

import torch

from autodrift.engineering_controller_failure_surface_guarded_repair_execution import _file_sha256
from autodrift.engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel import (
    DEFAULT_NEXT_BLOCKER,
    run_guardrailed_candidate_fresh_holdout_triad_delta_panel,
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
        model.actor_mean.bias[1].sub_(bias_delta)
        model.actor_mean.bias[2].add_(bias_delta)
    torch.save(
        {
            "model_state": {key: value.detach().cpu() for key, value in model.state_dict().items()},
            "config": _model_config(),
        },
        path,
    )


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_m2791_sources(path: Path, source: Path, base: Path, candidate: Path) -> None:
    path.mkdir(parents=True)
    (path / "summary.json").write_text(
        json.dumps(
            {
                "status_pass": True,
                "gate_matrix_pass": True,
                "training_objective_row_count": 18,
                "candidate_checkpoint_hash": _file_sha256(candidate),
                "base_candidate_checkpoint_hash": _file_sha256(base),
            }
        ),
        encoding="utf-8",
    )
    (path / "checkpoint_manifest.json").write_text(
        json.dumps(
            {
                "source_reference_checkpoint_hash": _file_sha256(source),
                "base_candidate_checkpoint_hash": _file_sha256(base),
                "candidate_checkpoint_hash": _file_sha256(candidate),
                "candidate_checkpoint_written": True,
                "checkpoint_promoted": False,
            }
        ),
        encoding="utf-8",
    )
    objective_rows = []
    index = 0
    for role in ORDINARY_ROLE_FAMILIES:
        for axis in DYNAMICS_AXES:
            for stress in STRESS_FAMILIES:
                objective_rows.append(
                    {
                        "training_objective_row_id": f"m2791_objective_{index:03d}",
                        "source_curriculum_row_id": f"source_{role}_{axis}_{stress}",
                        "role_family": role,
                        "dynamics_axis": axis,
                        "stress_family": stress,
                        "training_seeds_requested": 3,
                        "proof_seeds_requested": 2,
                        "behavior_retention_seed_count": 4,
                        "future_training_allowed": True,
                        "future_execution_allowed": True,
                        "actor_visible_label": False,
                        "mitigation_reference_context_only": False,
                        "ranking_admissible": False,
                        "obstacle_clearance_guard_required": True,
                        "road_margin_objective_allowed": True,
                        "yaw_rate_objective_allowed": True,
                        "final_speed_guard_required": True,
                        "throttle_brake_conflict_guard_required": True,
                        "action_delta_diagnostic_only": True,
                        "claim_boundary": "test",
                    }
                )
                index += 1
    _write_rows(
        path / "training_objective_rows.csv",
        objective_rows,
        [
            "training_objective_row_id",
            "source_curriculum_row_id",
            "role_family",
            "dynamics_axis",
            "stress_family",
            "training_seeds_requested",
            "proof_seeds_requested",
            "behavior_retention_seed_count",
            "future_training_allowed",
            "future_execution_allowed",
            "actor_visible_label",
            "mitigation_reference_context_only",
            "ranking_admissible",
            "obstacle_clearance_guard_required",
            "road_margin_objective_allowed",
            "yaw_rate_objective_allowed",
            "final_speed_guard_required",
            "throttle_brake_conflict_guard_required",
            "action_delta_diagnostic_only",
            "claim_boundary",
        ],
    )
    _write_rows(
        path / "mitigation_reference_guard_rows.csv",
        [
            {
                "source_guard_id": "mitigation_a",
                "candidate_id": "mitigation_a",
                "role_family": "mitigation",
                "dynamics_axis": "fresh_fault_delay_noise",
                "seed": 11,
                "mitigation_reference": True,
                "ordinary_denominator_allowed": False,
                "future_training_allowed": False,
                "future_execution_allowed": False,
            }
        ],
        [
            "source_guard_id",
            "candidate_id",
            "role_family",
            "dynamics_axis",
            "seed",
            "mitigation_reference",
            "ordinary_denominator_allowed",
            "future_training_allowed",
            "future_execution_allowed",
        ],
    )
    (path / "gate_matrix.csv").write_text("gate_id,status_pass\nm2791_gate,True\n", encoding="utf-8")
    (path / "behavior_retention_gate_rows.csv").write_text(
        "gate_id,status_pass\nbehavior_guard,True\n",
        encoding="utf-8",
    )


def _write_m2787_sources(path: Path) -> None:
    path.mkdir(parents=True)
    (path / "summary.json").write_text(
        json.dumps(
            {
                "status_pass": True,
                "gate_matrix_pass": True,
                "paired_delta_row_count": 72,
                "horizon_steps": 3,
                "fresh_holdout_seed_indices": [4, 5],
                "m2784_seed_indices": [0, 3],
            }
        ),
        encoding="utf-8",
    )
    (path / "paired_delta_rows.csv").write_text(
        "pair_id,seed_index\nm2787_pair_a,4\nm2787_pair_b,7\n",
        encoding="utf-8",
    )
    (path / "gate_matrix.csv").write_text("gate_id,status_pass\nm2787_gate,True\n", encoding="utf-8")


def test_guardrailed_candidate_fresh_holdout_triad_panel_writes_claim_safe_deltas(tmp_path):
    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2793.md"
    follow_up_manifest = tmp_path / "m2794.json"
    m2792_audit = tmp_path / "m2792.md"
    m2791_dir = tmp_path / "m2791"
    m2787_dir = tmp_path / "m2787"
    m2782_dir = tmp_path / "m2782"
    source_checkpoint = tmp_path / "source.pt"
    base_checkpoint = tmp_path / "base.pt"
    candidate_checkpoint = tmp_path / "candidate.pt"
    m2792_audit.write_text("# audit\n", encoding="utf-8")
    _write_checkpoint(source_checkpoint, bias_delta=0.0)
    _write_checkpoint(base_checkpoint, bias_delta=0.03)
    _write_checkpoint(candidate_checkpoint, bias_delta=0.05)
    _write_m2791_sources(m2791_dir, source_checkpoint, base_checkpoint, candidate_checkpoint)
    _write_m2787_sources(m2787_dir)
    m2782_dir.mkdir()
    (m2782_dir / "summary.json").write_text(json.dumps({"status_pass": True}), encoding="utf-8")

    summary = run_guardrailed_candidate_fresh_holdout_triad_delta_panel(
        output_dir,
        m2792_audit=m2792_audit,
        m2791_dir=m2791_dir,
        m2787_dir=m2787_dir,
        m2782_dir=m2782_dir,
        source_checkpoint=source_checkpoint,
        base_candidate_checkpoint=base_checkpoint,
        candidate_checkpoint=candidate_checkpoint,
        follow_up_manifest=follow_up_manifest,
        doc_path=doc_path,
        device="cpu",
        seed_start_index=8,
        seed_count=2,
        horizon_steps=4,
        milestone="m2793-test",
        next_blocker="m2794-test",
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_source_only_belief_stress_guardrailed_candidate_fresh_holdout_triad_delta_panel_preflight_pass"
    )
    assert summary["m2791_status_pass"] is True
    assert summary["m2787_status_pass"] is True
    assert summary["m2782_status_pass"] is True
    assert summary["source_checkpoint_hash"] != summary["base_candidate_checkpoint_hash"]
    assert summary["base_candidate_checkpoint_hash"] != summary["candidate_checkpoint_hash"]
    assert summary["seed_start_index"] == 8
    assert summary["seed_count"] == 2
    assert summary["fresh_holdout_seed_indices"] == [8, 9]
    assert summary["fresh_holdout_seed_indices_disjoint_from_previous"] is True
    assert summary["horizon_longer_than_m2787"] is True
    assert summary["objective_row_count"] == 18
    assert summary["triad_execution_row_count"] == 108
    assert summary["candidate_minus_source_delta_row_count"] == 36
    assert summary["candidate_minus_base_delta_row_count"] == 36
    assert summary["proof_gate_row_count"] == 16
    assert summary["generalization_gate_row_count"] == 9
    assert summary["behavior_retention_gate_row_count"] == 6
    assert summary["promotion_guard_row_count"] == 4
    assert summary["gate_matrix_row_count"] == 35
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["actor_visible_stress_admission_curriculum_labels_detected"] is False
    assert summary["mitigation_reference_rows_guarded"] is True
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["m2794_follow_up_manifest_registered"] is True

    execution_rows = _read_csv(output_dir / "triad_execution_rows.csv")
    source_delta_rows = _read_csv(output_dir / "candidate_minus_source_delta_rows.csv")
    base_delta_rows = _read_csv(output_dir / "candidate_minus_base_delta_rows.csv")
    mitigation_rows = _read_csv(output_dir / "mitigation_reference_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    m2794 = json.loads(follow_up_manifest.read_text())

    assert len(execution_rows) == 108
    assert len(source_delta_rows) == 36
    assert len(base_delta_rows) == 36
    assert len(gate_rows) == 35
    assert {row["checkpoint_subject"] for row in execution_rows} == {"source", "base_candidate", "candidate"}
    assert {row["seed_index"] for row in execution_rows} == {"8", "9"}
    assert {row["seed_index"] for row in source_delta_rows} == {"8", "9"}
    assert {row["seed_index"] for row in base_delta_rows} == {"8", "9"}
    assert {row["delta_family"] for row in source_delta_rows} == {"candidate_minus_source"}
    assert {row["delta_family"] for row in base_delta_rows} == {"candidate_minus_base"}
    assert {row["observation_shape"] for row in execution_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in execution_rows} == {str(ACTION_DIM)}
    assert {row["actor_visible_label"] for row in execution_rows} == {"False"}
    assert {row["hidden_or_oracle_actor_inputs_required"] for row in execution_rows} == {"False"}
    assert {row["diagnostic_only"] for row in execution_rows} == {"True"}
    assert {row["paired_row_complete"] for row in source_delta_rows + base_delta_rows} == {"True"}
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
    assert m2794["id"] == DEFAULT_NEXT_BLOCKER
    assert m2794["training_stage"]["stage"] == "process"
    assert doc_path.exists()
