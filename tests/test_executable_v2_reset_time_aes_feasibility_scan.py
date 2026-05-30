from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.executable_v2_reset_time_aes_sampler_diagnostic import (
    ACCEPTED,
    REJECT_AEB_FEASIBLE,
    REJECT_THRESHOLD,
    TARGET_LABEL,
)
from autodrift import executable_v2_reset_time_aes_feasibility_scan as scan


def _env_config(
    *,
    speed: float = 20.0,
    max_threshold_score: float | None = None,
) -> dict[str, object]:
    obstacle: dict[str, object] = {
        "enabled": True,
        "allowed_labels": [TARGET_LABEL],
        "require_aeb_infeasible": True,
        "distance_range": [18.0, 18.0],
        "half_width_range": [0.3, 0.3],
        "ego_half_width": 0.9,
        "safety_margin": 0.3,
        "brake_mu_fraction": 0.9,
        "conventional_lateral_mu_fraction": 0.42,
        "drift_lateral_mu_fraction": 0.85,
        "max_sample_attempts": 4,
    }
    if max_threshold_score is not None:
        obstacle["max_threshold_score"] = max_threshold_score
    return {
        "track_kind": "circle",
        "track_radius": 18.0,
        "speed_range": [speed, speed],
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
        "obstacle": obstacle,
    }


def _spec(source: str, profile: str, *, speed: float = 20.0, max_threshold_score: float | None = None) -> dict[str, object]:
    return {
        "v2_panel_spec_id": f"{source}::{profile}",
        "source_v1_bounded_panel_spec_id": source,
        "source_scenario_spec_id": f"{source}_scenario",
        "profile_name": profile,
        "v2_task_label": TARGET_LABEL,
        "labels_enter_actor_input": False,
        "v2_ranking_admissible_by_default": False,
        "reset_ready_spec": True,
        "reset_validation_required": True,
        "env_config": _env_config(speed=speed, max_threshold_score=max_threshold_score),
    }


def _reset_row(spec: dict[str, object], *, success: bool = False, seed: int = 7) -> dict[str, object]:
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


def _write_fixture(tmp_path: Path, specs: list[dict[str, object]]) -> tuple[Path, Path]:
    specs_path = tmp_path / "repaired.json"
    reset_path = tmp_path / "reset.csv"
    write_json(specs_path, {"executable_v2_panel_specs": specs})
    write_csv_rows(reset_path, [_reset_row(spec, seed=index + 7) for index, spec in enumerate(specs)])
    return specs_path, reset_path


def test_scan_finds_accepted_aes_cell(tmp_path: Path) -> None:
    specs_path, reset_path = _write_fixture(tmp_path, [_spec("src", "L0")])

    summary = scan.run_reset_time_aes_feasibility_scan(
        repaired_specs_path=specs_path,
        reset_rows_path=reset_path,
        output_dir=tmp_path / "out",
        distance_range=(18.0, 18.0),
        distance_count=1,
        half_width_range=(0.3, 0.3),
        half_width_count=1,
        expected_target_source_count=1,
        expected_target_profile_count_total=1,
    )

    assert summary["result_class"] == "reset_time_aes_feasibility_scan_full_support"
    assert summary["feasible_profile_count_total"] == 1
    assert summary["accepted_cell_count_total"] == 1
    assert summary["guardrail_violation_count"] == 0

    accepted = (tmp_path / "out" / "reset_time_aes_feasibility_accepted_cells.csv").read_text()
    assert TARGET_LABEL in accepted
    assert ACCEPTED in accepted


def test_aeb_only_grid_has_zero_accepted_cells(tmp_path: Path) -> None:
    specs_path, reset_path = _write_fixture(tmp_path, [_spec("src", "L0")])

    summary = scan.run_reset_time_aes_feasibility_scan(
        repaired_specs_path=specs_path,
        reset_rows_path=reset_path,
        output_dir=tmp_path / "out",
        distance_range=(80.0, 80.0),
        distance_count=1,
        half_width_range=(0.3, 0.3),
        half_width_count=1,
        expected_target_source_count=1,
        expected_target_profile_count_total=1,
    )

    assert summary["result_class"] == "reset_time_aes_feasibility_scan_no_support"
    assert summary["accepted_cell_count_total"] == 0
    reject_counts = (tmp_path / "out" / "reset_time_aes_feasibility_reject_reason_counts.csv").read_text()
    assert REJECT_AEB_FEASIBLE in reject_counts


def test_threshold_filter_rejects_otherwise_aes_cell(tmp_path: Path) -> None:
    specs_path, reset_path = _write_fixture(tmp_path, [_spec("src", "L0", max_threshold_score=0.0)])

    summary = scan.run_reset_time_aes_feasibility_scan(
        repaired_specs_path=specs_path,
        reset_rows_path=reset_path,
        output_dir=tmp_path / "out",
        distance_range=(18.0, 18.0),
        distance_count=1,
        half_width_range=(0.3, 0.3),
        half_width_count=1,
        expected_target_source_count=1,
        expected_target_profile_count_total=1,
    )

    assert summary["accepted_cell_count_total"] == 0
    reject_counts = (tmp_path / "out" / "reset_time_aes_feasibility_reject_reason_counts.csv").read_text()
    assert REJECT_THRESHOLD in reject_counts


def test_profile_and_source_summaries_aggregate_counts(tmp_path: Path) -> None:
    specs_path, reset_path = _write_fixture(
        tmp_path,
        [
            _spec("src", "fast", speed=20.0),
            _spec("src", "slow", speed=10.0),
        ],
    )

    summary = scan.run_reset_time_aes_feasibility_scan(
        repaired_specs_path=specs_path,
        reset_rows_path=reset_path,
        output_dir=tmp_path / "out",
        distance_range=(18.0, 18.0),
        distance_count=1,
        half_width_range=(0.3, 0.3),
        half_width_count=1,
        expected_target_source_count=1,
        expected_target_profile_count_total=2,
    )

    assert summary["result_class"] == "reset_time_aes_feasibility_scan_partial_support"
    assert summary["target_profile_count_total"] == 2
    assert summary["feasible_profile_count_total"] == 1
    assert summary["accepted_cell_count_total"] == 1

    source_rows = (tmp_path / "out" / "reset_time_aes_feasibility_source_summary.csv").read_text()
    assert "src,src_scenario,2,1,1" in source_rows


def test_claim_boundary_blocks_payload_reset_and_ranking_claims() -> None:
    rows = scan.claim_boundary_rows()
    by_claim = {row["claim"]: row for row in rows}

    assert by_claim["reset_time_aes_feasibility_scan_helper"]["admissible"] is True
    assert by_claim["source_repair_payload_generated"]["admissible"] is False
    assert by_claim["reset_feasibility_repaired"]["admissible"] is False
    assert by_claim["controller_family_ranking"]["admissible"] is False
