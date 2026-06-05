import csv
import json
from pathlib import Path

import torch

from autodrift.engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight import (
    DEFAULT_NEXT_BLOCKER,
    run_clearance_localized_corrective_training_preflight,
)
from autodrift.engineering_controller_route_a_source_only_belief_stress_short_training_continuation_preflight import (
    DYNAMICS_AXES,
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


def _write_checkpoint(path: Path, *, steer_bias: float = 0.0):
    model = ActorCritic(
        obs_dim=P0_OBSERVATION_DIM,
        act_dim=ACTION_DIM,
        hidden_size=16,
        actor_encoder="human_view_online_gru",
        action_sequence_horizon=1,
    )
    with torch.no_grad():
        model.actor_mean.bias[0].add_(float(steer_bias))
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {
            "model_state": {
                key: value.detach().cpu() for key, value in model.state_dict().items()
            },
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


def _aggregate_rows():
    rows: list[dict[str, object]] = []
    index = 0

    def add(group_family, role, axis, stress, count, negative, mean_delta):
        nonlocal index
        rows.append(
            {
                "aggregate_id": f"agg_{index:03d}",
                "group_family": group_family,
                "group_key": f"role_family={role}",
                "delta_family": "all",
                "role_family": role,
                "dynamics_axis": axis,
                "stress_family": stress,
                "seed_index": "all",
                "row_count": count,
                "negative_clearance_count": negative,
                "positive_clearance_count": count - negative,
                "zero_clearance_count": 0,
                "negative_clearance_rate": negative / count,
                "mean_clearance_delta_m": mean_delta,
                "median_clearance_delta_m": mean_delta,
                "min_clearance_delta_m": mean_delta,
                "max_clearance_delta_m": mean_delta,
                "mean_minimum_road_margin_delta_m": 0.001,
                "mean_final_speed_delta_mps": 0.001,
                "yaw_rate_lower_count": count,
                "throttle_brake_conflict_zero_count": count,
                "all_rows_diagnostic_only": True,
                "ranking_admissible_count": 0,
                "winner_selected_count": 0,
                "claim_boundary": "test",
            }
        )
        index += 1

    add("role_family", "drift_required_recovery", "all", "all", 48, 48, -0.002)
    add("role_family", "stable_aes", "all", "all", 48, 36, -0.0015)
    add("role_family", "stable_avoidable", "all", "all", 48, 1, 0.003)
    stable_aes_bucket_negatives = iter([6, 7, 7, 6, 5, 5])
    for role in ("drift_required_recovery", "stable_aes", "stable_avoidable"):
        for axis in DYNAMICS_AXES:
            for stress in STRESS_FAMILIES:
                if role == "drift_required_recovery":
                    negative = 8
                    mean_delta = -0.002
                elif role == "stable_aes":
                    negative = next(stable_aes_bucket_negatives)
                    mean_delta = -0.001
                else:
                    negative = 1 if axis == DYNAMICS_AXES[0] and stress == STRESS_FAMILIES[0] else 0
                    mean_delta = 0.003
                add("role_dynamics_stress", role, axis, stress, 8, negative, mean_delta)
    return rows


def _clearance_rows():
    rows: list[dict[str, object]] = []
    index = 0
    for role in ("drift_required_recovery", "stable_aes", "stable_avoidable"):
        for axis in DYNAMICS_AXES:
            for stress in STRESS_FAMILIES:
                for seed_index in range(4):
                    for delta_family in ("candidate_minus_source", "candidate_minus_base"):
                        if role == "stable_avoidable":
                            clearance = -0.0001 if seed_index == 0 and axis == DYNAMICS_AXES[0] and stress == STRESS_FAMILIES[0] and delta_family == "candidate_minus_source" else 0.001
                        elif role == "stable_aes":
                            clearance = -0.001 if seed_index < 3 else 0.001
                        else:
                            clearance = -0.002
                        rows.append(
                            {
                                "atlas_row_id": f"atlas_{index:03d}",
                                "delta_family": delta_family,
                                "pair_id": f"pair_{index:03d}",
                                "role_family": role,
                                "dynamics_axis": axis,
                                "stress_family": stress,
                                "seed_index": seed_index,
                                "seed": 266100 + seed_index,
                                "clearance_delta_m": clearance,
                                "clearance_regression": clearance < 0,
                                "mean_action_delta_l1": 0.0002,
                                "diagnostic_only": True,
                                "ranking_admissible": False,
                                "winner_selected": False,
                                "claim_scope": "test",
                                "forbidden_interpretation": "test",
                            }
                        )
                        index += 1
    return rows


def _write_m2796_sources(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    (path / "summary.json").write_text(
        json.dumps(
            {
                "status_pass": True,
                "gate_matrix_pass": True,
                "clearance_regression_row_count": 144,
                "clearance_regression_aggregate_row_count": 21,
            }
        ),
        encoding="utf-8",
    )
    _write_rows(path / "clearance_regression_aggregate_rows.csv", _aggregate_rows())
    _write_rows(path / "clearance_regression_rows.csv", _clearance_rows())
    _write_rows(
        path / "gate_matrix.csv",
        [
            {
                "gate_id": "m2796_gate",
                "gate_tier": "proof",
                "gate_family": "artifact",
                "status_pass": True,
                "observed": "ok",
                "expected": "ok",
                "row_count": 1,
                "failure_type": "",
                "claim_boundary": "test",
            }
        ],
    )
    _write_rows(
        path / "mitigation_reference_guard_rows.csv",
        [
            {
                "source_guard_id": "mitigation_a",
                "candidate_id": "mitigation_a",
                "role_family": "unavoidable_mitigation",
                "dynamics_axis": "fresh_nominal_or_role_default",
                "seed": 267100,
                "mitigation_reference": True,
                "ordinary_denominator_allowed": False,
                "future_training_allowed": False,
                "future_execution_allowed": False,
                "context_only": True,
                "actor_visible_allowed": False,
                "included_in_training_rows": False,
                "included_in_proof_denominator": False,
                "status_pass": True,
                "guard_family": "test",
                "claim_boundary": "test",
            }
        ],
    )


def test_m2799_clearance_localized_corrective_training_preflight_writes_candidate_and_audit_manifest(tmp_path):
    source_checkpoint = tmp_path / "source.pt"
    base_checkpoint = tmp_path / "base.pt"
    start_checkpoint = tmp_path / "start.pt"
    _write_checkpoint(source_checkpoint, steer_bias=0.0)
    _write_checkpoint(base_checkpoint, steer_bias=0.001)
    _write_checkpoint(start_checkpoint, steer_bias=0.002)

    m2798_design = tmp_path / "m2798.md"
    m2797_audit = tmp_path / "m2797.md"
    m2798_design.write_text("# design\n", encoding="utf-8")
    m2797_audit.write_text("# audit\n", encoding="utf-8")

    m2796_dir = tmp_path / "m2796"
    _write_m2796_sources(m2796_dir)
    m2793_dir = tmp_path / "m2793"
    m2793_dir.mkdir()
    (m2793_dir / "summary.json").write_text('{"status_pass": true}\n', encoding="utf-8")
    m2791_dir = tmp_path / "m2791"
    m2791_dir.mkdir()
    (m2791_dir / "summary.json").write_text('{"status_pass": true}\n', encoding="utf-8")
    (m2791_dir / "checkpoint_manifest.json").write_text(
        '{"candidate_checkpoint_hash": "start_hash"}\n',
        encoding="utf-8",
    )

    output_dir = tmp_path / "run"
    doc_path = tmp_path / "m2799.md"
    follow_up_manifest = tmp_path / "m2800.json"
    summary = run_clearance_localized_corrective_training_preflight(
        output_dir,
        m2798_design=m2798_design,
        m2797_audit=m2797_audit,
        m2796_dir=m2796_dir,
        m2793_dir=m2793_dir,
        m2791_dir=m2791_dir,
        source_checkpoint=source_checkpoint,
        base_candidate_checkpoint=base_checkpoint,
        candidate_checkpoint=start_checkpoint,
        follow_up_manifest=follow_up_manifest,
        doc_path=doc_path,
        device="cpu",
        target_training_seeds_per_bucket=4,
        proof_seeds_per_bucket=2,
        stable_avoidable_retention_seed_count=4,
        behavior_retention_seed_count=4,
        max_updates=1,
        milestone="m2799-test",
        next_blocker="m2800-test",
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_source_only_belief_stress_clearance_localized_corrective_training_preflight_pass"
    )
    assert summary["training_objective_row_count"] == 18
    assert summary["target_objective_row_count"] == 12
    assert summary["retention_objective_row_count"] == 6
    assert summary["training_run_row_count"] == 48
    assert summary["target_proof_probe_row_count"] == 24
    assert summary["stable_avoidable_retention_probe_row_count"] == 24
    assert summary["proof_holdout_probe_row_count"] == 48
    assert summary["proof_gate_row_count"] == 14
    assert summary["generalization_gate_row_count"] == 6
    assert summary["behavior_retention_gate_row_count"] == 7
    assert summary["promotion_guard_row_count"] == 4
    assert summary["gate_matrix_row_count"] == 31
    assert summary["candidate_checkpoint_written"] is True
    assert summary["checkpoint_behavior_changed"] is True
    assert summary["candidate_checkpoint_hash"] != summary["start_candidate_checkpoint_hash"]
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["actor_visible_atlas_or_role_labels_detected"] is False
    assert summary["mitigation_reference_rows_guarded"] is True
    assert summary["target_negative_clearance_count"] == 84
    assert summary["target_row_count"] == 96
    assert summary["drift_required_recovery_negative_count"] == 48
    assert summary["stable_aes_negative_count"] == 36
    assert summary["stable_avoidable_negative_clearance_count"] == 1
    assert summary["obstacle_clearance_guard_hard_before_objectives"] is True
    assert summary["checkpoint_promoted"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["success_rate_computed"] is False
    assert summary["repair_success_claim_made"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False
    assert summary["m2800_follow_up_manifest_registered"] is True

    checkpoint_manifest = json.loads((output_dir / "checkpoint_manifest.json").read_text())
    objective_rows = _read_csv(output_dir / "training_objective_rows.csv")
    training_rows = _read_csv(output_dir / "training_run_rows.csv")
    proof_rows = _read_csv(output_dir / "proof_probe_rows.csv")
    behavior_rows = _read_csv(output_dir / "behavior_retention_gate_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    m2800 = json.loads(follow_up_manifest.read_text())

    assert Path(checkpoint_manifest["candidate_checkpoint"]).exists()
    assert checkpoint_manifest["behavior_changed"] is True
    assert checkpoint_manifest["checkpoint_promoted"] is False
    assert checkpoint_manifest["stable_avoidable_retention_guard_required"] is True
    assert {row["objective_family"] for row in objective_rows} == {
        "target_clearance_correction",
        "stable_avoidable_retention",
    }
    assert {row["role_family"] for row in training_rows} == {
        "drift_required_recovery",
        "stable_aes",
    }
    assert "stable_avoidable" in {row["role_family"] for row in proof_rows}
    assert {row["observation_shape"] for row in training_rows + proof_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in training_rows + proof_rows} == {str(ACTION_DIM)}
    assert {row["actor_visible_label"] for row in training_rows + proof_rows} == {"False"}
    assert {row["hidden_or_oracle_actor_inputs_required"] for row in training_rows + proof_rows} == {"False"}
    assert all(row["status_pass"] == "True" for row in behavior_rows)
    assert all(row["status_pass"] == "True" for row in gate_rows)
    assert m2800["id"] == DEFAULT_NEXT_BLOCKER
    assert m2800["training_stage"]["stage"] == "process"
    assert doc_path.exists()
