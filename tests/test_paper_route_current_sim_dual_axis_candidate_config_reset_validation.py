from __future__ import annotations

from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift import paper_route_current_sim_dual_axis_candidate_config_reset_validation as reset_validation


CANDIDATE_FIELDNAMES = [
    "candidate_id",
    "source_repair_spec_id",
    "repair_family",
    "candidate_config_path",
    "reward_patch_count",
    "curriculum_patch_count",
    "guardrail_patch_scope",
    "guardrail_patch_count",
    "mixed_collision_guardrail_required",
    "inside_run_dir",
    "active_config_overwritten",
    "loaded_into_environment",
    "environment_reset_started",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]
MATRIX_FIELDNAMES = [
    "candidate_id",
    "source_repair_spec_id",
    "reward_patch_ids",
    "curriculum_patch_ids",
    "reward_patch_count",
    "curriculum_patch_count",
    "candidate_config_path",
    "active_config_overwritten",
    "loaded_into_environment",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]
GUARDRAIL_FIELDNAMES = [
    "candidate_id",
    "guardrail_scope_id",
    "guardrail_patch_count",
    "mixed_collision_guardrail_required",
    "candidate_config_path",
    "active_config_overwritten",
    "loaded_into_environment",
    "repair_execution_started",
    "training_started",
    "ranking_admissible",
    "winner_selected",
]
CLAIM_FIELDNAMES = ["claim", "admissible", "reason"]


class _FakeConfig:
    def __init__(self, data):
        self.data = dict(data)
        self.raise_on_reset = bool(self.data.get("raise_on_reset", False))


class _FakeEnv:
    def __init__(self, config):
        self.config = config
        self.step_count = 0

    def reset(self, seed: int):
        if self.config.raise_on_reset:
            raise RuntimeError("synthetic reset failure")
        return np.full(72, float(seed % 7), dtype=np.float32), {"reset_only": True}

    def close(self) -> None:
        pass


def _payload(candidate_id: str, *, mixed: bool = False, include_env_config: bool = True) -> dict[str, object]:
    payload: dict[str, object] = {
        "candidate_id": candidate_id,
        "source_repair_spec_id": f"{candidate_id}_spec",
        "repair_family": "guarded_offtrack_containment_repair" if mixed else "offtrack_containment_repair",
        "source_slice_axis": "role_family",
        "source_slice_value": "R2_handling_limit_drift_capable_avoidance" if mixed else "R0_stable_avoidable",
        "priority_tier": "P1",
        "reward_overlay": [
            {"patch_id": f"{candidate_id}_reward_{index}", "target_key": f"reward.{index}", "delta_value": "0.1"}
            for index in range(3)
        ],
        "curriculum_overlay": [
            {"patch_id": f"{candidate_id}_curriculum_0", "target_key": "curriculum.0", "delta_value": "1.2"}
        ],
        "guardrail_overlay": {"scope_id": "global_guardrail_scope", "guardrail_patch_count": 284},
        "mixed_guarded_requirements": {"collision_guardrail_required": mixed},
        "claim_boundary": {
            "active_config_overwritten": False,
            "loaded_into_environment": False,
            "environment_reset_started": False,
            "repair_execution_started": False,
            "training_started": False,
            "ranking_admissible": False,
            "winner_selected": False,
        },
    }
    if include_env_config:
        payload["env_config"] = {
            "history_length": 1,
            "action_history_mode": "full",
            "include_privileged_params": False,
            "wheel_observation_mode": "none",
        }
    return payload


def _write_source_dir(tmp_path: Path, *, include_env_config: bool = True) -> Path:
    source = tmp_path / "source"
    config_dir = source / "candidate_configs"
    config_dir.mkdir(parents=True)
    candidate_ids = ["candidate_a", "candidate_b"]
    candidate_rows = []
    matrix_rows = []
    guardrail_rows = []
    for index, candidate_id in enumerate(candidate_ids):
        mixed = index == 1
        path = config_dir / f"{candidate_id}.json"
        write_json(path, _payload(candidate_id, mixed=mixed, include_env_config=include_env_config))
        candidate_rows.append(
            {
                "candidate_id": candidate_id,
                "source_repair_spec_id": f"{candidate_id}_spec",
                "repair_family": "guarded_offtrack_containment_repair" if mixed else "offtrack_containment_repair",
                "candidate_config_path": str(path),
                "reward_patch_count": 3,
                "curriculum_patch_count": 1,
                "guardrail_patch_scope": "global_guardrail_scope",
                "guardrail_patch_count": 284,
                "mixed_collision_guardrail_required": mixed,
                "inside_run_dir": True,
                "active_config_overwritten": False,
                "loaded_into_environment": False,
                "environment_reset_started": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
        matrix_rows.append(
            {
                "candidate_id": candidate_id,
                "source_repair_spec_id": f"{candidate_id}_spec",
                "reward_patch_ids": "|".join(f"{candidate_id}_reward_{i}" for i in range(3)),
                "curriculum_patch_ids": f"{candidate_id}_curriculum_0",
                "reward_patch_count": 3,
                "curriculum_patch_count": 1,
                "candidate_config_path": str(path),
                "active_config_overwritten": False,
                "loaded_into_environment": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
        guardrail_rows.append(
            {
                "candidate_id": candidate_id,
                "guardrail_scope_id": "global_guardrail_scope",
                "guardrail_patch_count": 284,
                "mixed_collision_guardrail_required": mixed,
                "candidate_config_path": str(path),
                "active_config_overwritten": False,
                "loaded_into_environment": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
            }
        )
    write_json(source / "summary.json", {"result_class": "current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_pass"})
    write_json(
        source / "candidate_config_generation_manifest.json",
        {"result_class": "current_sim_dual_axis_offtrack_guardrail_candidate_config_generation_pass"},
    )
    write_json(source / "active_config_safety_report.json", {"active_config_overwritten": False})
    write_csv_rows(source / "candidate_config_rows.csv", candidate_rows, fieldnames=CANDIDATE_FIELDNAMES)
    write_csv_rows(source / "candidate_patch_reference_matrix.csv", matrix_rows, fieldnames=MATRIX_FIELDNAMES)
    write_csv_rows(source / "candidate_guardrail_scope_rows.csv", guardrail_rows, fieldnames=GUARDRAIL_FIELDNAMES)
    write_csv_rows(
        source / "claim_boundary.csv",
        [{"claim": "environment_reset_or_rollout", "admissible": False, "reason": "blocked"}],
        fieldnames=CLAIM_FIELDNAMES,
    )
    return source


def test_candidate_config_reset_validation_passes_with_synthetic_env_config(tmp_path: Path, monkeypatch) -> None:
    source = _write_source_dir(tmp_path, include_env_config=True)
    monkeypatch.setattr(reset_validation, "build_env_config", lambda data: _FakeConfig(data))
    monkeypatch.setattr(reset_validation, "AutoDriftEnv", _FakeEnv)

    summary = reset_validation.run_candidate_config_reset_validation(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_candidate_config_count=2,
        eval_seed_base=100,
    )

    assert summary["result_class"] == "current_sim_dual_axis_candidate_config_reset_validation_pass"
    assert summary["static_validation_pass_count"] == 2
    assert summary["schema_incomplete_candidate_count"] == 0
    assert summary["effective_config_written_count"] == 2
    assert summary["effective_config_outside_run_dir_count"] == 0
    assert summary["environment_reset_attempt_count"] == 2
    assert summary["environment_reset_success_count"] == 2
    assert summary["environment_step_count"] == 0
    assert summary["policy_action_executed"] is False
    assert summary["guardrail_violation_count"] == 0


def test_candidate_config_reset_validation_fails_closed_when_schema_lacks_env_config(tmp_path: Path) -> None:
    source = _write_source_dir(tmp_path, include_env_config=False)

    summary = reset_validation.run_candidate_config_reset_validation(
        source_dir=source,
        output_dir=tmp_path / "out",
        target_candidate_config_count=2,
        eval_seed_base=100,
    )

    assert summary["result_class"] == "current_sim_dual_axis_candidate_config_reset_validation_fail"
    assert summary["static_validation_pass_count"] == 2
    assert summary["schema_incomplete_candidate_count"] == 2
    assert summary["effective_config_written_count"] == 0
    assert summary["environment_reset_attempt_count"] == 0
    assert summary["environment_reset_started"] is False
    assert summary["environment_step_count"] == 0
    effective_rows = (tmp_path / "out" / "effective_config_rows.csv").read_text(encoding="utf-8")
    assert "missing_env_config_for_reset" in effective_rows
    persisted = read_json(tmp_path / "out" / "summary.json")
    assert persisted["repair_execution_started"] is False
    assert persisted["current_sim_verdict_claim_made"] is False
