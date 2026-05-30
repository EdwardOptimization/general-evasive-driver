from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.executable_v2_reset_time_aes_sampler_diagnostic import REJECT_AEB_FEASIBLE
from autodrift import executable_v2_reset_time_aes_source_repair_v2 as repair


def _env_config(label: str, *, distance: list[float], half_width: list[float]) -> dict[str, object]:
    return {
        "track_kind": "circle",
        "track_radius": 18.0,
        "speed_range": [20.0, 20.0],
        "friction_limited_speed": False,
        "randomization": {
            "mu_range": [1.0, 1.0],
            "mass_scale_range": [1.0, 1.0],
            "cg_shift_range": [0.0, 0.0],
            "inertia_scale_range": [1.0, 1.0],
            "tire_stiffness_scale_range": [1.0, 1.0],
            "drive_scale_range": [1.0, 1.0],
            "brake_scale_range": [1.0, 1.0],
            "actuator_tau_scale_range": [1.0, 1.0],
        },
        "obstacle": {
            "enabled": True,
            "allowed_labels": [label],
            "require_aeb_infeasible": label == "aes_feasible",
            "distance_range": distance,
            "half_width_range": half_width,
            "ego_half_width": 0.9,
            "safety_margin": 0.3,
            "brake_mu_fraction": 0.9,
            "conventional_lateral_mu_fraction": 0.42,
            "drift_lateral_mu_fraction": 0.85,
            "max_sample_attempts": 10,
        },
    }


def _spec(source: str, profile: str, label: str, *, distance: list[float], half_width: list[float]) -> dict[str, object]:
    return {
        "v2_panel_spec_id": f"{source}::{profile}",
        "source_v1_bounded_panel_spec_id": source,
        "source_scenario_spec_id": f"{source}_scenario",
        "profile_name": profile,
        "v2_task_label": label,
        "hidden_dynamics_bucket": "nominal",
        "road_boundary_bucket": "nominal",
        "obstacle_timing_bucket": "medium",
        "obstacle_lateral_bucket": "center",
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "reset_ready_spec": True,
        "reset_validation_required": True,
        "env_config": _env_config(label, distance=distance, half_width=half_width),
    }


def _reset_row(spec: dict[str, object], *, success: bool, seed: int) -> dict[str, object]:
    return {
        "v2_panel_spec_id": spec["v2_panel_spec_id"],
        "source_v1_bounded_panel_spec_id": spec["source_v1_bounded_panel_spec_id"],
        "source_scenario_spec_id": spec["source_scenario_spec_id"],
        "profile_name": spec["profile_name"],
        "v2_task_label": spec["v2_task_label"],
        "reset_success": success,
        "eval_seed": seed,
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
    }


def _write_fixture(tmp_path: Path) -> tuple[Path, Path]:
    specs = [
        _spec("aes_src", "L0", "aes_feasible", distance=[80.0, 80.0], half_width=[0.3, 0.3]),
        _spec("aes_src", "L1", "aes_feasible", distance=[80.0, 80.0], half_width=[0.3, 0.3]),
        _spec("aeb_src", "L0", "aeb_feasible", distance=[80.0, 80.0], half_width=[0.3, 0.3]),
    ]
    reset_rows = [
        _reset_row(specs[0], success=False, seed=7),
        _reset_row(specs[1], success=False, seed=8),
        _reset_row(specs[2], success=True, seed=9),
    ]
    specs_path = tmp_path / "repaired.json"
    reset_path = tmp_path / "reset.csv"
    write_json(specs_path, {"executable_v2_panel_specs": specs})
    write_csv_rows(reset_path, reset_rows)
    return specs_path, reset_path


def test_aeb_feasible_only_candidate_is_not_selected(tmp_path: Path) -> None:
    specs_path, reset_path = _write_fixture(tmp_path)
    specs = repair.load_repaired_specs(specs_path)
    reset_rows = repair.load_reset_rows(reset_path)
    groups = repair.failed_aes_source_groups(repaired_specs=specs, reset_rows=reset_rows)
    source_specs = groups["aes_src"]
    original = repair.candidate_obstacles(source_specs[0]["env_config"], main_attempt_budget=10)[0]

    score = repair.score_candidate_for_source(
        source_key="aes_src",
        specs=source_specs,
        candidate=original,
        main_attempt_budget=10,
    )

    assert score["accepted_profile_count"] == 0
    assert score["dominant_reject_reason"] == REJECT_AEB_FEASIBLE
    assert score["attempt_count_by_reject_reason"][REJECT_AEB_FEASIBLE] == 20


def test_selects_reset_time_aes_only_candidate_and_preserves_controls(tmp_path: Path) -> None:
    specs_path, reset_path = _write_fixture(tmp_path)

    summary = repair.run_reset_time_aes_source_repair_v2(
        repaired_specs_path=specs_path,
        reset_rows_path=reset_path,
        output_dir=tmp_path / "out",
        target_source_count=1,
        target_profile_count=2,
        target_repaired_spec_count=3,
        main_attempt_budget=10,
    )

    assert summary["result_class"] == "reset_time_aes_source_repair_v2_pass"
    assert summary["target_source_count"] == 1
    assert summary["accepted_profile_count_total"] == 2
    assert summary["attempt_count_by_label"]["aes_feasible"] >= 2
    assert summary["attempt_count_by_reject_reason"]["accepted"] == 2
    assert summary["summary_aggregation_version"] == "row_and_attempt_counts_v1"
    assert summary["labels_enter_actor_input_count"] == 0
    assert summary["ranking_admissible_by_default_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is False

    payload = read_json(tmp_path / "out" / "repaired_targeted_reset_executable_v2_panel_specs.json")
    rows = payload["executable_v2_panel_specs"]
    aes_rows = [row for row in rows if row["source_v1_bounded_panel_spec_id"] == "aes_src"]
    aeb_row = next(row for row in rows if row["source_v1_bounded_panel_spec_id"] == "aeb_src")
    assert {row["profile_name"] for row in aes_rows} == {"L0", "L1"}
    assert {row["reset_time_aes_source_repair_candidate"] for row in aes_rows} != {"original_reset_replay"}
    assert all(row["env_config"]["obstacle"]["allowed_labels"] == ["aes_feasible"] for row in aes_rows)
    assert all(row["env_config"]["obstacle"]["require_aeb_infeasible"] is True for row in aes_rows)
    assert all(row["v2_ranking_admissible_by_default"] is False for row in aes_rows)
    assert aeb_row["reset_time_aes_source_repair_applied"] is False
    assert aeb_row["env_config"]["obstacle"]["allowed_labels"] == ["aeb_feasible"]


def test_claim_boundary_blocks_reset_repair_and_ranking_claims() -> None:
    rows = repair.claim_boundary_rows()
    by_claim = {row["claim"]: row for row in rows}

    assert by_claim["reset_time_aes_source_repair_plan"]["admissible"] is True
    assert by_claim["reset_feasibility_repaired"]["admissible"] is False
    assert by_claim["controller_family_ranking"]["admissible"] is False
