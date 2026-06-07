from pathlib import Path

import numpy as np

from autodrift.artifacts import read_json, write_csv_rows, write_json
import autodrift.engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_bounded_direct_action_fitting_preflight as m3065


def _read_csv(path: Path) -> list[dict[str, str]]:
    import csv

    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_sources(root: Path, *, raw_action_trace_used_as_target: bool = False) -> dict[str, Path]:
    m3061_dir = root / "m3061"
    m3055_dir = root / "m3055"
    tensor_dir = m3061_dir / "target_tensors"
    tensor_dir.mkdir(parents=True)
    m3055_dir.mkdir(parents=True)

    m3064_design = root / "m3064.md"
    m3064_design.write_text(
        "admit_m3065_bounded_direct_action_fitting_preflight_without_validation_or_promotion\n",
        encoding="utf-8",
    )
    m3063_synthesis = root / "m3063.md"
    m3063_synthesis.write_text("continue_to_m3064_fitting_admission_design\n", encoding="utf-8")
    m3062_audit = root / "m3062.md"
    m3062_audit.write_text(
        "accept_m3061_target_tensor_rerun_claim_safe_route_to_m3063_branch_synthesis\n",
        encoding="utf-8",
    )

    write_json(
        m3061_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "target_tensor_file_exists_count": 4,
            "target_tensor_missing_count": 0,
        },
    )
    write_json(m3055_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True})
    write_csv_rows(
        m3055_dir / "fitting_contract_rows.csv",
        [
            {
                "contract_id": "contract-1",
                "output_semantics": "direct_action",
                "actor_observation_shape": "72",
                "actor_action_shape": "3",
                "base_policy_required_at_runtime": "False",
            }
        ],
    )
    write_csv_rows(
        m3055_dir / "loss_family_rows.csv",
        [{"loss_family_id": "loss-1", "loss_family": "offtrack_recovery", "status_pass": True}],
    )

    behavior_rows = []
    file_rows = []
    for index in range(1, 5):
        obs = np.zeros((2, 72), dtype=np.float32)
        obs[:, 0] = float(index)
        obs[:, 1] = np.asarray([0.0, 1.0], dtype=np.float32)
        target = np.zeros((2, 3), dtype=np.float32)
        target[:, 0] = 0.1 * float(index)
        target[:, 1] = 0.05
        target[:, 2] = -0.05
        mask = np.ones((2, 3), dtype=np.float32)
        weight = np.ones((2, 3), dtype=np.float32)
        tensor_path = tensor_dir / f"target-{index}.npz"
        np.savez_compressed(
            tensor_path,
            observation_trace=obs,
            raw_action_trace=np.zeros((2, 3), dtype=np.float32),
            next_observation_trace=obs,
            target_action=target,
            target_action_mask=mask,
            target_loss_weight=weight,
            raw_action_trace_used_as_target=np.asarray(raw_action_trace_used_as_target and index == 1),
        )
        behavior_rows.append(
            {
                "target_tensor_row_id": f"target-row-{index}",
                "measurement_episode_id": f"episode-{index}",
                "binding_role": "candidate" if index % 2 else "parent",
                "task_family": "T4",
                "source_edge": "unit",
                "window_tag": "unit",
                "raw_trace_termination_reason": "off_track",
                "numeric_target_tensor_materialized": "True",
                "target_tensor_path": str(tensor_path),
                "target_rule_family": "actor_visible_road_center_terminal_recovery_window",
                "target_labels_actor_visible": "False",
                "target_provenance_actor_visible": "False",
                "hidden_oracle_actor_input_required": "False",
                "ttc_actor_input_required": "False",
                "target_tensor_quality_claim_made": "False",
            }
        )
        file_rows.append(
            {
                "target_tensor_file_index_row_id": f"file-{index}",
                "target_tensor_row_id": f"target-row-{index}",
                "target_tensor_path": str(tensor_path),
                "target_tensor_file_exists": "True",
            }
        )
    write_csv_rows(m3061_dir / "behavior_target_tensor_rows.csv", behavior_rows)
    write_csv_rows(m3061_dir / "target_tensor_file_index_rows.csv", file_rows)
    write_csv_rows(
        m3061_dir / "target_tensor_weight_rows.csv",
        [{"weight_row_id": "weight-1", "loss_family": "offtrack_recovery", "status_pass": True}],
    )
    return {
        "m3064_design": m3064_design,
        "m3063_synthesis": m3063_synthesis,
        "m3062_audit": m3062_audit,
        "m3061_dir": m3061_dir,
        "m3055_dir": m3055_dir,
    }


def test_run_m3065_writes_direct_action_candidate_and_followup(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m3065, "EXPECTED_TARGET_ROWS", 4)
    monkeypatch.setattr(m3065, "EXPECTED_MASKED_STEPS", 8)
    monkeypatch.setattr(m3065, "EXPECTED_WEIGHT_SUM", 24.0)
    paths = _write_sources(tmp_path)

    summary = m3065.run_bounded_direct_action_fitting_preflight(
        m3064_design=paths["m3064_design"],
        m3063_synthesis=paths["m3063_synthesis"],
        m3062_audit=paths["m3062_audit"],
        m3061_dir=paths["m3061_dir"],
        m3055_dir=paths["m3055_dir"],
        output_dir=tmp_path / "m3065",
        doc_path=tmp_path / "m3065.md",
        follow_up_manifest=tmp_path / "m3066.json",
    )

    assert summary["status_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["bounded_offline_direct_action_fitting_run"] is True
    assert summary["validation_run"] is False
    assert summary["ranking_run"] is False
    assert summary["checkpoint_mutated"] is False
    assert summary["output_semantics"] == "direct_action"
    assert summary["fitting_dataset_row_count"] == 4
    assert summary["fit_row_count"] == 3
    assert summary["internal_accounting_row_count"] == 1
    assert summary["final_fit_weighted_mse"] <= summary["initial_fit_weighted_mse"]
    assert Path(summary["candidate_direct_action_reflex_layer"]).exists()
    assert (tmp_path / "m3066.json").exists()
    loss_rows = _read_csv(tmp_path / "m3065" / "fitting_loss_trace_rows.csv")
    assert loss_rows[1]["status_pass"] == "True"
    assert read_json(tmp_path / "m3065" / "summary.json")["selected_next_action"] == m3065.NEXT_ID


def test_run_m3065_fails_closed_when_raw_action_is_target(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(m3065, "EXPECTED_TARGET_ROWS", 4)
    monkeypatch.setattr(m3065, "EXPECTED_MASKED_STEPS", 8)
    monkeypatch.setattr(m3065, "EXPECTED_WEIGHT_SUM", 24.0)
    paths = _write_sources(tmp_path, raw_action_trace_used_as_target=True)

    summary = m3065.run_bounded_direct_action_fitting_preflight(
        m3064_design=paths["m3064_design"],
        m3063_synthesis=paths["m3063_synthesis"],
        m3062_audit=paths["m3062_audit"],
        m3061_dir=paths["m3061_dir"],
        m3055_dir=paths["m3055_dir"],
        output_dir=tmp_path / "m3065",
        doc_path=tmp_path / "m3065.md",
        follow_up_manifest=tmp_path / "m3066.json",
    )

    assert summary["status_pass"] is False
    assert summary["bounded_offline_direct_action_fitting_run"] is False
    assert not Path(summary["candidate_direct_action_reflex_layer"]).exists()
    dataset_rows = _read_csv(tmp_path / "m3065" / "fitting_dataset_rows.csv")
    assert dataset_rows[0]["raw_action_trace_used_as_target"] == "True"
    assert dataset_rows[0]["status_pass"] == "False"
