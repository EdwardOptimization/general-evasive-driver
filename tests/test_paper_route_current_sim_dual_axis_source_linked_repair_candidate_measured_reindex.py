from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_dual_axis_source_linked_repair_candidate_measured_reindex as runner
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _episode(reset_key: str, *, idx: int = 0) -> dict[str, object]:
    return {
        "workload_id": f"workload_{idx}",
        "reset_target_key": reset_key,
        "selected_checkpoint_path": f"checkpoint_{idx % 2}.pt",
        "profile_name": "L0_current_masked",
        "pack_id": "pack_a",
        "success": False,
        "collision": False,
        "termination_reason": "off_track",
        "outcome_bucket": "off_track_noncollision_noncompletion",
        "return": -1.0,
        "steps": 10,
        "min_clearance_margin": 1.0,
        "max_off_track_overshoot": 0.1,
        "time_to_first_off_track_s": 0.5,
        "high_sideslip_fraction": 0.0,
        "action_rate_mean": 0.01,
    }


def _write_sources(tmp_path: Path, *, measured_key: str = "pack|spec|abc") -> tuple[Path, Path]:
    reset_dir = tmp_path / "reset"
    measured_dir = tmp_path / "measured"
    reset_dir.mkdir()
    measured_dir.mkdir()
    write_json(reset_dir / "summary.json", {"result_class": "reset_fail_closed"})
    write_json(measured_dir / "summary.json", {"result_class": "measured_pass"})
    write_csv_rows(
        reset_dir / "source_linked_family_rows.csv",
        [
            {
                "candidate_id": "c01_source_linked_geometry_timing_containment",
                "candidate_family": "source_linked_geometry_timing_containment",
                "matched_effective_candidate_count": 1,
            },
            {
                "candidate_id": runner.EXCLUDED_CANDIDATE_ID,
                "candidate_family": "source_linked_outcome_failure_surface_containment",
                "matched_effective_candidate_count": 0,
            },
        ],
    )
    write_csv_rows(
        reset_dir / "source_linked_scenario_rows.csv",
        [
            {
                "candidate_id": "c01_source_linked_geometry_timing_containment",
                "candidate_family": "source_linked_geometry_timing_containment",
                "reset_target_key": "pack|spec|abc",
            },
            {
                "candidate_id": runner.EXCLUDED_CANDIDATE_ID,
                "candidate_family": "source_linked_outcome_failure_surface_containment",
                "reset_target_key": "pack|spec|abc",
            },
        ],
    )
    write_csv_rows(reset_dir / "reset_target_rows.csv", [{"reset_target_key": "pack|spec|abc"}])
    write_csv_rows(measured_dir / "episode_rows.csv", [_episode(measured_key)])
    return reset_dir, measured_dir


def test_measured_reindex_passes_and_excludes_c04(tmp_path: Path) -> None:
    reset_dir, measured_dir = _write_sources(tmp_path)

    summary = runner.run_source_linked_repair_candidate_measured_reindex(
        source_reset_dir=reset_dir,
        source_measured_dir=measured_dir,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == runner.RESULT_PASS
    assert summary["exact_reset_key_coverage"] is True
    assert summary["matched_candidate_family_count"] == 1
    assert summary["expected_matched_candidate_family_count"] == 1
    assert summary["reindexed_membership_row_count"] == 1
    assert summary["c04_included_as_measured"] is False
    assert summary["guardrail_violation_count"] == 0

    rows = runner.read_csv_rows(tmp_path / "out" / "reindexed_episode_membership_rows.csv")
    assert len(rows) == 1
    assert rows[0]["candidate_id"] == "c01_source_linked_geometry_timing_containment"
    assert read_json(tmp_path / "out" / "summary.json")["result_class"] == runner.RESULT_PASS


def test_measured_reindex_fails_on_reset_key_mismatch(tmp_path: Path) -> None:
    reset_dir, measured_dir = _write_sources(tmp_path, measured_key="pack|spec|different")

    summary = runner.run_source_linked_repair_candidate_measured_reindex(
        source_reset_dir=reset_dir,
        source_measured_dir=measured_dir,
        output_dir=tmp_path / "out",
    )

    assert summary["result_class"] == runner.RESULT_FAIL
    assert summary["exact_reset_key_coverage"] is False
    assert summary["reset_keys_not_in_measured_count"] == 1
    assert summary["measured_keys_not_in_reset_count"] == 1
    assert "lineage_invalid" in summary["failure_types_observed"]
