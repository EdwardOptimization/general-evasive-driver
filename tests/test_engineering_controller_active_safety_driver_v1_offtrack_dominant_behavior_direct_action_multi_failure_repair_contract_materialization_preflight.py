from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
import autodrift.engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_contract_materialization_preflight as m3071


def _episode_row(index: int, *, binding: str, task: str, termination: str, success: bool, collision: bool) -> dict[str, object]:
    return {
        "measurement_episode_id": f"unit-episode-{index:04d}",
        "binding_role": binding,
        "task_family": task,
        "termination_reason": termination,
        "outcome_bucket": "success" if success else ("collision_failure" if collision else f"{termination}_failure"),
        "success": success,
        "collision": collision,
        "action_clip_fraction": 0.02,
        "raw_action_abs_max": 1.4,
        "min_clearance_margin": 5.0,
        "high_sideslip_fraction": 0.6 if termination == "off_track" else 0.1,
    }


def _measurement_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index in range(1, 9):
        rows.append(
            _episode_row(
                index,
                binding="candidate" if index % 2 else "parent",
                task="T4" if index <= 4 else "T5",
                termination="",
                success=True,
                collision=False,
            )
        )
    for index in range(9, 12):
        rows.append(
            _episode_row(
                index,
                binding="candidate" if index % 2 else "parent",
                task="T5",
                termination="obstacle_collision",
                success=False,
                collision=True,
            )
        )
    for index in range(12, 28):
        rows.append(
            _episode_row(
                index,
                binding="candidate" if index % 2 else "parent",
                task="T4" if index % 3 else "T5",
                termination="off_track",
                success=False,
                collision=index == 12,
            )
        )
    for index in range(28, 33):
        rows.append(
            _episode_row(
                index,
                binding="candidate" if index % 2 else "parent",
                task="T4",
                termination="speed_too_low",
                success=False,
                collision=False,
            )
        )
    return rows


def _write_sources(m3069_dir: Path, m3067_dir: Path) -> None:
    m3069_dir.mkdir(parents=True)
    m3067_dir.mkdir(parents=True)
    write_json(
        m3069_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "actor_contract_shape_72_action_3": True,
            "m3067_claim_boundary_rows_pass": True,
            "runtime_base_policy_required": False,
            "candidate_output_semantics": "direct_action_clipped",
            "candidate_output_components": ["steer", "throttle", "brake"],
            "measurement_raw_action_abs_max": 2.0,
        },
    )
    requirement_rows = [
        {
            "requirement_id": f"req-{family}",
            "requirement_family": family,
            "priority": "p0" if family in {"offtrack_containment_recovery", "t5_collision_guard", "claim_boundary_guard"} else "p1",
            "affected_group": "all",
            "row_count": "1",
        }
        for family in m3071.REQUIREMENT_FAMILIES
    ]
    write_csv_rows(m3069_dir / "direct_action_repair_requirement_rows.csv", requirement_rows)
    write_csv_rows(m3069_dir / "gate_matrix.csv", [{"gate_id": "gate-1", "status_pass": True}])
    write_csv_rows(m3069_dir / "claim_boundary_rows.csv", [{"claim_id": "claim-1", "status_pass": True}])
    write_csv_rows(m3067_dir / "measurement_episode_rows.csv", _measurement_rows())


def test_materialize_multi_failure_repair_contract_preserves_contract_boundaries(tmp_path: Path) -> None:
    m3069_dir = tmp_path / "m3069"
    m3067_dir = tmp_path / "m3067"
    output_dir = tmp_path / "m3071"
    follow_up_manifest = tmp_path / "m3072.json"
    doc_path = tmp_path / "m3071.md"
    audit_path = tmp_path / "m3070.md"
    audit_path.write_text("# audit\n", encoding="utf-8")
    _write_sources(m3069_dir, m3067_dir)

    summary = m3071.materialize(
        m3070_audit=audit_path,
        m3069_dir=m3069_dir,
        m3067_dir=m3067_dir,
        output_dir=output_dir,
        follow_up_manifest=follow_up_manifest,
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["measurement_episode_row_count"] == 32
    assert summary["direct_action_repair_contract_row_count"] == 1
    assert summary["direct_action_loss_family_row_count"] == 6
    assert summary["direct_action_row_admission_row_count"] == 32
    assert summary["direct_action_guard_family_row_count"] >= 9
    assert summary["runtime_base_policy_required"] is False
    assert summary["repair_success_claim_made"] is False

    contract_rows = read_csv_rows(output_dir / "direct_action_repair_contract_rows.csv")
    assert contract_rows[0]["observation_shape"] == "72"
    assert contract_rows[0]["action_shape"] == "3"
    assert contract_rows[0]["runtime_base_policy_required"] == "False"

    loss_rows = read_csv_rows(output_dir / "direct_action_loss_family_rows.csv")
    assert {row["requirement_family"] for row in loss_rows} == set(m3071.LOSS_FAMILIES)

    admission_rows = read_csv_rows(output_dir / "direct_action_row_admission_rows.csv")
    assert len(admission_rows) == 32
    assert all(row["target_labels_actor_visible"] == "False" for row in admission_rows)

    guard_rows = read_csv_rows(output_dir / "direct_action_guard_family_rows.csv")
    assert all(row["status_pass"] == "True" for row in guard_rows)

    claim_rows = read_csv_rows(output_dir / "claim_boundary_rows.csv")
    assert next(row for row in claim_rows if row["claim_id"] == "m3071-fitted_policy_quality")["claim_made"] == "False"

    follow_up = read_json(follow_up_manifest)
    assert follow_up["id"] == m3071.NEXT_ID
    assert follow_up["status"] == "pending"
