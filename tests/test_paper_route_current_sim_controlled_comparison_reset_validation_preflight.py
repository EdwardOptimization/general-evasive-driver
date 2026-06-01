from __future__ import annotations

import csv
from pathlib import Path

from autodrift import paper_route_current_sim_controlled_comparison_executable_spec_materialization as materialization
from autodrift import paper_route_current_sim_controlled_comparison_reset_validation_preflight as reset_preflight
from autodrift.artifacts import read_json, write_json
from autodrift.paper_route_current_sim_controlled_comparison_reset_validation_preflight import (
    contract_row_for_spec,
    run_current_sim_reset_validation_preflight,
)


def _write_specs(path: Path, count: int = 2) -> list[dict[str, object]]:
    summary = materialization.materialize_executable_specs(output_dir=path.parent / "materialization")
    assert summary["result_class"] == "current_sim_controlled_comparison_executable_spec_materialization_pass"
    specs = read_json(path.parent / "materialization" / "executable_task_specs.json")["executable_task_specs"][:count]
    write_json(path, {"protocol": "test", "executable_task_specs": specs})
    return specs


def test_current_sim_reset_validation_preflight_runs_reset_only(tmp_path: Path) -> None:
    specs_path = tmp_path / "specs.json"
    output_dir = tmp_path / "out"
    _write_specs(specs_path, count=2)

    summary = run_current_sim_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=output_dir,
        eval_seed_base=215300,
        target_spec_count=2,
        expected_observation_dim=72,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "current_sim_controlled_comparison_reset_validation_preflight_pass"
    assert summary["task_id"] == "m2154-paper-route-current-sim-controlled-comparison-reset-validation-implementation-and-run"
    assert summary["expected_materialization_semantics"] == "current_sim_executable_spec_v0"
    assert summary["expected_paper_validity_status"] == "current_sim_executable_candidate_not_reset_validated"
    assert summary["input_executable_spec_count"] == 2
    assert summary["reset_attempt_count"] == 2
    assert summary["reset_success_count"] == 2
    assert summary["reset_failure_count"] == 0
    assert summary["observation_dimension_failure_count"] == 0
    assert summary["observation_finite_count"] == 2
    assert summary["obstacle_initialized_count"] == 2
    assert summary["contract_violation_count"] == 0
    assert summary["metadata_missing_count"] == 0
    assert summary["forbidden_key_violation_count"] == 0
    assert summary["task_family_quota_pass"] is True
    assert summary["source_family_template_quota_pass"] is True
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is True
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    persisted = read_json(output_dir / "summary.json")
    assert persisted["next_blocker"] == "next-audit"
    assert (output_dir / "reset_rows.csv").exists()
    assert (output_dir / "reset_failure_rows.csv").exists()
    assert (output_dir / "contract_rows.csv").exists()
    assert (output_dir / "reset_distribution_by_seed_source.csv").exists()
    assert (output_dir / "claim_boundary.csv").exists()
    assert (output_dir / "run_state.json").exists()


def test_current_sim_reset_validation_prefers_spec_eval_seed_override(tmp_path: Path, monkeypatch) -> None:
    specs_path = tmp_path / "specs.json"
    output_dir = tmp_path / "out"
    specs = _write_specs(specs_path, count=2)
    specs[0]["eval_seed_override"] = "101"
    specs[1]["eval_seed_override"] = 102
    write_json(specs_path, {"protocol": "test", "executable_task_specs": specs})

    captured_eval_seeds: list[int] = []

    def fake_reset_current_sim_spec(
        *,
        spec: dict[str, object],
        eval_seed: int,
        expected_observation_dim: int | None,
    ) -> dict[str, object]:
        captured_eval_seeds.append(int(eval_seed))
        metadata = reset_preflight.current_sim_metadata(spec)
        return {
            **metadata,
            "eval_seed": int(eval_seed),
            "reset_success": True,
            "error_type": "",
            "error_message": "",
            "observation_length": expected_observation_dim,
            "expected_observation_length": expected_observation_dim,
            "observation_dimension_matches": True,
            "observation_finite": True,
            "obstacle_initialized": True,
            "reset_sampled_obstacle_label": "avoidable",
            "initial_mu": 0.8,
            "speed_ref": 20.0,
            "obstacle_distance": 30.0,
            "obstacle_half_width": 1.0,
            "contract_violation_count": 0,
            "environment_reset_started": True,
            "environment_rollout_started": False,
            "policy_action_executed": False,
            "measured_rollout_started": False,
            "training_started": False,
            "replay_started": False,
            "ppo_used": False,
            "promoted": False,
            "private_holdout_used": False,
            "actor_input_contract_changed": False,
            "profile_specific_tuning": False,
            "controller_family_ranking_claim_made": False,
            "finite_window_vs_gru_conclusion_made": False,
            "paper_level_claim_made": False,
            "level3_self_id_claim_made": False,
        }

    monkeypatch.setattr(reset_preflight, "reset_current_sim_spec", fake_reset_current_sim_spec)

    summary = reset_preflight.run_current_sim_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=output_dir,
        eval_seed_base=215300,
        target_spec_count=2,
        expected_observation_dim=72,
        seed_source_mode="prefer_spec_eval_seed_override",
        next_blocker="next-audit",
    )

    assert captured_eval_seeds == [101, 102]
    assert summary["result_class"] == "current_sim_controlled_comparison_reset_validation_preflight_pass"
    assert summary["seed_source_mode"] == "prefer_spec_eval_seed_override"
    assert summary["expected_seed_source_counts"] == {"eval_seed_override": 2}
    assert summary["seed_source_counts"] == {"eval_seed_override": 2}
    assert summary["seed_source_quota_pass"] is True
    assert summary["seed_source_parse_failure_count"] == 0

    with (output_dir / "reset_rows.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["actual_eval_seed"] for row in rows] == ["101", "102"]
    assert [row["seed_source"] for row in rows] == ["eval_seed_override", "eval_seed_override"]


def test_current_sim_contract_rejects_wrong_materialization_semantics(tmp_path: Path) -> None:
    specs_path = tmp_path / "specs.json"
    spec = _write_specs(specs_path, count=1)[0]
    assert contract_row_for_spec(spec)["contract_violation_count"] == 0

    wrong_semantics = dict(spec)
    wrong_semantics["materialization_semantics"] = "comparison_support_smoke_proxy"
    row = contract_row_for_spec(wrong_semantics)

    assert row["materialization_semantics_matches_expected"] is False
    assert row["contract_violation_count"] >= 1


def test_current_sim_contract_accepts_custom_materialization_semantics(tmp_path: Path) -> None:
    specs_path = tmp_path / "specs.json"
    spec = _write_specs(specs_path, count=1)[0]
    repaired = dict(spec)
    repaired["materialization_semantics"] = "current_sim_offtrack_support_repair_materialization_v0"
    repaired["paper_validity_status"] = "current_sim_offtrack_support_candidate_not_reset_validated"

    default_row = contract_row_for_spec(repaired)
    custom_row = contract_row_for_spec(
        repaired,
        expected_materialization_semantics="current_sim_offtrack_support_repair_materialization_v0",
        expected_paper_validity_status="current_sim_offtrack_support_candidate_not_reset_validated",
    )

    assert default_row["materialization_semantics_matches_expected"] is False
    assert default_row["paper_validity_status_matches_expected"] is False
    assert custom_row["materialization_semantics_matches_expected"] is True
    assert custom_row["paper_validity_status_matches_expected"] is True
    assert custom_row["contract_violation_count"] == 0


def test_current_sim_reset_validation_fails_closed_on_metadata_gap(tmp_path: Path) -> None:
    specs_path = tmp_path / "specs.json"
    specs = _write_specs(specs_path, count=1)
    broken = dict(specs[0])
    broken["task_family"] = ""
    write_json(specs_path, {"protocol": "test", "executable_task_specs": [broken]})

    summary = run_current_sim_reset_validation_preflight(
        executable_task_specs_path=specs_path,
        output_dir=tmp_path / "out",
        eval_seed_base=215300,
        target_spec_count=1,
        expected_observation_dim=72,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "current_sim_controlled_comparison_reset_validation_preflight_fail"
    assert summary["metadata_missing_count"] == 1
