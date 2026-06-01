from __future__ import annotations

from pathlib import Path

from autodrift import paper_route_current_sim_repeat_seed_diversity_combined_outcome_audit as audit
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _episode(
    workload_id: str,
    profile_name: str,
    outcome_bucket: str,
    *,
    repeat_id: str = "",
    success: bool = False,
    collision: bool = False,
) -> dict[str, object]:
    return {
        "workload_id": workload_id,
        "profile_name": profile_name,
        "training_repeat_id": repeat_id,
        "outcome_bucket": outcome_bucket,
        "termination_reason": "off_track" if outcome_bucket == "off_track_noncollision_noncompletion" else "",
        "success": str(success),
        "collision": str(collision),
        "return": 1.0,
        "steps": 10,
        "min_clearance_margin": 0.1,
    }


def _write_output_dir(path: Path, rows: list[dict[str, object]]) -> None:
    path.mkdir(parents=True)
    write_csv_rows(path / "episode_rows.csv", rows)
    write_json(path / "summary.json", {"guardrail_violation_count": 0})


def _checkpoint(path: Path, content: bytes) -> str:
    path.write_bytes(content)
    return str(path)


def test_repeat_seed_diversity_audit_flags_low_support_and_identical_vectors(tmp_path: Path) -> None:
    original_dir = tmp_path / "original"
    repeat_dir = tmp_path / "repeat"
    rows_original = [
        _episode("task_a::L0", "L0", "success_obstacle_pass", success=True),
        _episode("task_b::L0", "L0", "off_track_noncollision_noncompletion"),
    ]
    rows_repeat = [
        _episode("r1::task_a::L0", "L0", "success_obstacle_pass", repeat_id="repeat_1_seed_21761", success=True),
        _episode("r1::task_b::L0", "L0", "off_track_noncollision_noncompletion", repeat_id="repeat_1_seed_21761"),
        _episode("r2::task_a::L0", "L0", "success_obstacle_pass", repeat_id="repeat_2_seed_21762", success=True),
        _episode("r2::task_b::L0", "L0", "off_track_noncollision_noncompletion", repeat_id="repeat_2_seed_21762"),
    ]
    _write_output_dir(original_dir, rows_original)
    _write_output_dir(repeat_dir, rows_repeat)

    ckpt_0 = _checkpoint(tmp_path / "c0.pt", b"base")
    ckpt_1 = _checkpoint(tmp_path / "c1.pt", b"repeat-one")
    ckpt_2 = _checkpoint(tmp_path / "c2.pt", b"repeat-two")
    original_workload = tmp_path / "original_workload.csv"
    repeat_workload = tmp_path / "repeat_workload.csv"
    write_csv_rows(original_workload, [{"workload_id": "task_a::L0", "profile_name": "L0", "checkpoint_path": ckpt_0}])
    write_csv_rows(
        repeat_workload,
        [
            {
                "workload_id": "r1::task_a::L0",
                "base_workload_id": "task_a::L0",
                "training_repeat_id": "repeat_1_seed_21761",
                "profile_name": "L0",
                "checkpoint_path": ckpt_1,
            },
            {
                "workload_id": "r2::task_a::L0",
                "base_workload_id": "task_a::L0",
                "training_repeat_id": "repeat_2_seed_21762",
                "profile_name": "L0",
                "checkpoint_path": ckpt_2,
            },
        ],
    )

    summary = audit.run_repeat_seed_diversity_combined_outcome_audit(
        original_output_dir=original_dir,
        original_workload=original_workload,
        repeat_output_dir=repeat_dir,
        repeat_workload=repeat_workload,
        output_dir=tmp_path / "audit",
        expected_combined_episode_count=6,
        expected_repeat_count=3,
        expected_per_repeat_count=2,
        min_combined_success_count=4,
        max_combined_offtrack_rate=0.40,
        min_success_count_per_repeat=2,
    )

    assert summary["combined_episode_count"] == 6
    assert summary["comparison_ready"] is False
    assert summary["outcome_support_pass"] is False
    assert summary["seed_diversity_status"] == "suspicious_identical_repeat_outcome_vectors"
    assert summary["repeat_aggregate_equal"] is True
    assert summary["checkpoint_duplicate_count"] == 0
    assert (tmp_path / "audit" / "combined_repeat_aggregate.csv").exists()
    assert (tmp_path / "audit" / "profile_repeat_outcome_aggregate.csv").exists()
    assert (tmp_path / "audit" / "repeat_diversity_flags.csv").exists()

    claim_boundary = (tmp_path / "audit" / "comparison_readiness_claim_boundary.csv").read_text(encoding="utf-8")
    assert "controller_family_ranking,False" in claim_boundary


def test_repeat_seed_diversity_audit_passes_when_support_and_diversity_pass(tmp_path: Path) -> None:
    original_dir = tmp_path / "original"
    repeat_dir = tmp_path / "repeat"
    rows_original = [
        _episode("task_a::L0", "L0", "success_obstacle_pass", success=True),
        _episode("task_b::L0", "L0", "success_obstacle_pass", success=True),
    ]
    rows_repeat = [
        _episode("r1::task_a::L0", "L0", "success_obstacle_pass", repeat_id="repeat_1_seed_21761", success=True),
        _episode("r1::task_b::L0", "L0", "success_obstacle_pass", repeat_id="repeat_1_seed_21761", success=True),
        _episode("r2::task_a::L0", "L0", "success_obstacle_pass", repeat_id="repeat_2_seed_21762", success=True),
        _episode("r2::task_b::L1", "L1", "collision_failure", repeat_id="repeat_2_seed_21762", collision=True),
    ]
    _write_output_dir(original_dir, rows_original)
    _write_output_dir(repeat_dir, rows_repeat)

    ckpt_0 = _checkpoint(tmp_path / "c0.pt", b"base")
    ckpt_1 = _checkpoint(tmp_path / "c1.pt", b"repeat-one")
    ckpt_2 = _checkpoint(tmp_path / "c2.pt", b"repeat-two")
    original_workload = tmp_path / "original_workload.csv"
    repeat_workload = tmp_path / "repeat_workload.csv"
    write_csv_rows(original_workload, [{"workload_id": "task_a::L0", "profile_name": "L0", "checkpoint_path": ckpt_0}])
    write_csv_rows(
        repeat_workload,
        [
            {
                "workload_id": "r1::task_a::L0",
                "base_workload_id": "task_a::L0",
                "training_repeat_id": "repeat_1_seed_21761",
                "profile_name": "L0",
                "checkpoint_path": ckpt_1,
            },
            {
                "workload_id": "r2::task_a::L0",
                "base_workload_id": "task_a::L0",
                "training_repeat_id": "repeat_2_seed_21762",
                "profile_name": "L0",
                "checkpoint_path": ckpt_2,
            },
        ],
    )

    summary = audit.run_repeat_seed_diversity_combined_outcome_audit(
        original_output_dir=original_dir,
        original_workload=original_workload,
        repeat_output_dir=repeat_dir,
        repeat_workload=repeat_workload,
        output_dir=tmp_path / "audit",
        expected_combined_episode_count=6,
        expected_repeat_count=3,
        expected_per_repeat_count=2,
        min_combined_success_count=5,
        max_combined_offtrack_rate=0.20,
        min_success_count_per_repeat=1,
    )

    assert summary["comparison_ready"] is True
    assert summary["outcome_support_pass"] is True
    assert summary["seed_diversity_status"] == "pass"
    persisted = read_json(tmp_path / "audit" / "summary.json")
    assert persisted["result_class"] == "current_sim_repeat_seed_diversity_combined_outcome_audit_comparison_ready"
