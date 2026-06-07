from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.controller_family_full_rollout_execution import read_csv_rows
import autodrift.engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_bounded_fitting_preflight as m3073


def _write_target_tensor(path: Path, scale: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    steps = 32
    obs = np.zeros((steps, 72), dtype=np.float32)
    obs[:, 0] = np.linspace(-1.0, 1.0, steps, dtype=np.float32)
    obs[:, 1] = scale
    obs[:, 2] = np.linspace(0.5, -0.5, steps, dtype=np.float32)
    target = np.zeros((steps, 3), dtype=np.float32)
    target[:, 0] = np.clip(0.2 * obs[:, 0] + 0.05 * scale, -1.0, 1.0)
    target[:, 1] = np.clip(0.1 + 0.03 * scale, -1.0, 1.0)
    target[:, 2] = np.clip(0.04 * obs[:, 2], -1.0, 1.0)
    mask = np.ones((steps, 3), dtype=np.float32)
    weight = np.ones((steps, 3), dtype=np.float32)
    np.savez_compressed(
        path,
        observation_trace=obs,
        target_action=target,
        target_action_mask=mask,
        target_loss_weight=weight,
        raw_action_trace_used_as_target=np.asarray(False),
    )


def _write_sources(root: Path) -> tuple[Path, Path, Path, Path]:
    audit_path = root / "m3072.md"
    m3071_dir = root / "m3071"
    m3065_dir = root / "m3065"
    m3061_dir = root / "m3061"
    target_dir = m3061_dir / "target_tensors"
    m3071_dir.mkdir()
    m3065_dir.mkdir()
    m3061_dir.mkdir()
    audit_path.write_text(
        "accept_m3071_repair_contract_claim_safe_route_to_m3073_bounded_repair_fitting_preflight\n",
        encoding="utf-8",
    )
    write_json(
        m3071_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
        },
    )
    write_csv_rows(
        m3071_dir / "direct_action_repair_contract_rows.csv",
        [
            {
                "contract_id": "contract",
                "observation_shape": "72",
                "action_shape": "3",
                "output_semantics": "direct_action_clipped",
                "runtime_base_policy_required": "False",
            }
        ],
    )
    write_csv_rows(
        m3071_dir / "direct_action_loss_family_rows.csv",
        [{"requirement_family": family, "status_pass": True} for family in sorted(m3073.EXPECTED_REQUIREMENT_FAMILIES)],
    )
    write_csv_rows(
        m3071_dir / "direct_action_row_admission_rows.csv",
        [{"row_admission_id": f"row-{index}", "status_pass": True} for index in range(32)],
    )
    write_csv_rows(
        m3071_dir / "direct_action_guard_family_rows.csv",
        [{"guard_family": family, "status_pass": True} for family in sorted(m3073.EXPECTED_REQUIREMENT_FAMILIES)],
    )
    write_csv_rows(m3071_dir / "claim_boundary_rows.csv", [{"claim_id": "claim", "status_pass": True}])
    write_csv_rows(m3071_dir / "gate_matrix.csv", [{"gate_id": "gate", "status_pass": True}])
    write_json(
        m3065_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "candidate_direct_action_reflex_layer_exists": True,
        },
    )
    np.savez_compressed(
        m3065_dir / "candidate_direct_action_reflex_layer.npz",
        linear_weight=np.zeros((72, 3), dtype=np.float32),
        linear_bias=np.zeros((3,), dtype=np.float32),
    )
    fitting_rows = []
    index_rows = []
    for index in range(1, 25):
        target_path = target_dir / f"target-{index:04d}.npz"
        _write_target_tensor(target_path, scale=index / 24.0)
        split = "internal_accounting" if index % 4 == 0 else "fit"
        row = {
            "fitting_dataset_row_id": f"m3065-row-{index:04d}",
            "target_tensor_row_id": f"target-row-{index:04d}",
            "measurement_episode_id": f"episode-{index:04d}",
            "binding_role": "candidate" if index % 2 else "parent",
            "task_family": "T5" if index % 3 == 0 else "T4",
            "source_edge": "curved_boundary_obstacle|brake_fade_proxy" if index % 3 == 0 else "actuator_delay_step",
            "window_tag": "unit",
            "raw_trace_termination_reason": "off_track",
            "target_tensor_path": str(target_path),
            "split": split,
            "target_labels_actor_visible": False,
            "target_provenance_actor_visible": False,
            "hidden_oracle_actor_input_required": False,
            "ttc_actor_input_required": False,
            "target_quality_validated": False,
            "status_pass": True,
        }
        fitting_rows.append(row)
        index_rows.append({"target_tensor_row_id": row["target_tensor_row_id"], "target_tensor_path": str(target_path)})
    write_csv_rows(m3065_dir / "fitting_dataset_rows.csv", fitting_rows)
    write_json(m3061_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(m3061_dir / "target_tensor_file_index_rows.csv", index_rows)
    return audit_path, m3071_dir, m3065_dir, m3061_dir


def test_m3073_bounded_repair_fit_writes_candidate_and_claim_boundaries(tmp_path: Path) -> None:
    audit_path, m3071_dir, m3065_dir, m3061_dir = _write_sources(tmp_path)
    output_dir = tmp_path / "m3073"
    follow_up_manifest = tmp_path / "m3074.json"
    doc_path = tmp_path / "m3073.md"

    summary = m3073.run_bounded_repair_fitting_preflight(
        m3072_audit=audit_path,
        m3071_dir=m3071_dir,
        m3065_dir=m3065_dir,
        m3061_dir=m3061_dir,
        output_dir=output_dir,
        follow_up_manifest=follow_up_manifest,
        doc_path=doc_path,
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["repair_fitting_dataset_row_count"] == 24
    assert summary["fit_row_count"] == 18
    assert summary["internal_accounting_row_count"] == 6
    assert summary["candidate_direct_action_repair_reflex_layer_exists"] is True
    assert summary["runtime_base_policy_required"] is False
    assert summary["repair_success_claim_made"] is False

    dataset_rows = read_csv_rows(output_dir / "repair_fitting_dataset_rows.csv")
    assert len(dataset_rows) == 24
    assert all(row["target_labels_actor_visible"] == "False" for row in dataset_rows)
    assert any("t5_collision_guard" in row["repair_loss_families"] for row in dataset_rows)

    claim_rows = read_csv_rows(output_dir / "claim_boundary_rows.csv")
    assert next(row for row in claim_rows if row["claim_family"] == "closed_loop_repair_success")["claim_made"] == "False"

    with np.load(output_dir / "candidate_direct_action_repair_reflex_layer.npz", allow_pickle=False) as candidate:
        assert candidate["linear_weight"].shape == (72, 3)
        assert candidate["linear_bias"].shape == (3,)
        assert candidate["output_semantics"][0] == "direct_action_clipped"

    follow_up = read_json(follow_up_manifest)
    assert follow_up["id"] == m3073.NEXT_ID
    assert follow_up["status"] == "pending"
