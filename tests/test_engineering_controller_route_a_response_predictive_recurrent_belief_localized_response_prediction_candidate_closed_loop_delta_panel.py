from __future__ import annotations

import csv
from pathlib import Path

import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift import (
    engineering_controller_route_a_response_predictive_recurrent_belief_localized_response_prediction_candidate_closed_loop_delta_panel as m2868,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class _FakeModel:
    obs_dim = 72
    act_dim = 3
    actor_encoder = "human_view_online_gru"


def _write_source_artifacts(root: Path) -> dict[str, Path]:
    workload = root / "m1690.csv"
    specs = root / "specs.json"
    surface_rows = root / "surface_rows.csv"
    workload_rows = []
    spec_rows = []
    surface_payload = []
    for index in range(4):
        task_source_id = f"m1680-spec-{index:04d}"
        surface_id = "m2850_explanatory" if index < 2 else "fresh_disjoint"
        workload_rows.append(
            {
                "workload_id": f"{task_source_id}::L3_online_gru",
                "task_source_id": task_source_id,
                "profile_name": "L3_online_gru",
                "task_family": "T4",
                "source_edge": "capability_step_down|actuator_delay_step",
                "window_tag": "mapping_window_unspecified",
                "executable_source_family": "source_family",
                "env_template_family": "template",
                "strata": "all_72_specs",
                "profile_config_path": str(root / f"{task_source_id}.json"),
                "checkpoint_path": "unused-old-checkpoint.pt",
                "config_exists": True,
                "checkpoint_exists": True,
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
            }
        )
        write_json(root / f"{task_source_id}.json", {"env": {"history_length": 1}, "runtime": {}})
        spec_rows.append({"task_source_id": task_source_id, "env_config": {"history_length": 1, "max_steps": 480}})
        surface_payload.append(
            {
                "surface_row_id": f"m2857-surface-{surface_id}-{index + 1:04d}",
                "surface_id": surface_id,
                "pair_id": f"m2868-test-pair-{index + 1:04d}",
                "task_source_id": task_source_id,
                "profile_name": "L3_online_gru",
                "task_family": "T4",
                "source_edge": "capability_step_down|actuator_delay_step",
                "window_tag": "mapping_window_unspecified",
                "source_family_tag": "capability_step_down",
                "scenario_role_primary": "actuator_delay_step",
                "surface_role": "M2850 explanatory diagnostic trace" if index < 2 else "fresh disjoint telemetry trace",
                "source_from": "M2854 row localization" if index < 2 else "M1690 L3_online_gru disjoint row",
                "public_diagnostic_row": index < 2,
                "fresh_or_disjoint": index >= 2,
                "overlap_guard_required": False,
                "overlap_reason": "",
                "diagnostic_only": True,
                "ranking_admissible": False,
                "ordinary_success_denominator_allowed": False,
            }
        )
    write_csv_rows(workload, workload_rows)
    write_json(specs, {"executable_task_specs": spec_rows})
    write_csv_rows(surface_rows, surface_payload)

    m2867 = root / "m2867.md"
    m2867.write_text("decision: accept_m2866_route_to_m2868_closed_loop_delta_panel\n", encoding="utf-8")
    m2866_summary = root / "m2866-summary.json"
    write_json(
        m2866_summary,
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "candidate_checkpoint_written": True,
            "actor_contract_shape_72_action_3": True,
            "hidden_oracle_actor_input_required": False,
            "response_prediction_loss_mean": 0.25,
        },
    )
    baseline = root / "baseline.pt"
    candidate = root / "candidate.pt"
    baseline.write_bytes(b"baseline")
    candidate.write_bytes(b"candidate")
    return {
        "workload": workload,
        "specs": specs,
        "surface_rows": surface_rows,
        "m2867": m2867,
        "m2866_summary": m2866_summary,
        "baseline": baseline,
        "candidate": candidate,
    }


def test_m2868_writes_surface_separated_paired_deltas_and_blocks_overclaims(monkeypatch, tmp_path: Path) -> None:
    paths = _write_source_artifacts(tmp_path)
    output_dir = tmp_path / "m2868"
    doc_path = tmp_path / "m2868.md"
    follow_up = tmp_path / "m2869.json"

    def fake_load(path: Path, device: str):
        del path, device
        return _FakeModel(), {"model_state": {"actor_mean.weight": torch.zeros((3, 2))}}

    def fake_hash(path: Path) -> str:
        return Path(path).stem + "-hash"

    def fake_state_hash(state: dict[str, torch.Tensor]) -> str:
        return "state-" + str(len(state))

    def fake_run_workload_cell(**kwargs: object) -> dict[str, object]:
        workload_row = kwargs["workload_row"]
        profile_row = kwargs["profile_row"]
        subject = "candidate" if "candidate" in str(profile_row["checkpoint_path"]) else "baseline"
        task_index = int(str(workload_row["task_source_id"]).split("-")[-1])
        subject_offset = 0.05 if subject == "candidate" else 0.0
        return {
            "workload_id": workload_row["workload_id"],
            "task_source_id": workload_row["task_source_id"],
            "profile_name": workload_row["profile_name"],
            "task_family": workload_row["task_family"],
            "source_edge": workload_row["source_edge"],
            "window_tag": workload_row["window_tag"],
            "strata": workload_row["strata"],
            "executable_source_family": workload_row["executable_source_family"],
            "env_template_family": workload_row["env_template_family"],
            "profile_config_path": profile_row["config_path"],
            "checkpoint_path": profile_row["checkpoint_path"],
            "seed": kwargs["eval_seed"],
            "policy": "checkpoint",
            "steps": 12,
            "terminated": True,
            "truncated": False,
            "success": False,
            "collision": False,
            "obstacle_completed": False,
            "termination_reason": "off_track",
            "outcome_bucket": "diagnostic",
            "min_clearance_margin": float(task_index) / 100.0 + subject_offset,
            "min_obstacle_clearance": 1.0,
            "return": 1.0 + subject_offset,
            "speed_mean": 7.0,
            "high_sideslip_fraction": 0.0,
            "action_rate_mean": 0.1,
            "previous_command_norm_mean": 0.2,
            "current_action_norm_mean": 0.3,
            "action_trace_delta_mean": 0.4,
            "plan_horizon": 1,
        }

    monkeypatch.setattr(m2868, "load_actor_critic_checkpoint", fake_load)
    monkeypatch.setattr(m2868, "_file_sha256", fake_hash)
    monkeypatch.setattr(m2868, "model_state_sha256", fake_state_hash)
    monkeypatch.setattr(m2868, "run_workload_cell", fake_run_workload_cell)

    summary = m2868.run_localized_response_prediction_candidate_closed_loop_delta_panel(
        m1690_workload=paths["workload"],
        executable_specs=paths["specs"],
        m2867_audit=paths["m2867"],
        m2866_summary=paths["m2866_summary"],
        m2857_surface_rows=paths["surface_rows"],
        baseline_checkpoint=paths["baseline"],
        candidate_checkpoint=paths["candidate"],
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up,
        eval_seed_base=286800,
        row_count=4,
        horizon_steps=12,
        device="cpu",
    )

    assert summary["status_pass"] is True
    assert summary["surface_counts"] == {"fresh_disjoint": 2, "m2850_explanatory": 2}
    assert summary["paired_execution_row_count"] == 8
    assert summary["paired_delta_row_count"] == 4
    assert summary["surface_delta_row_count"] == 2
    assert summary["actor_contract_guard_rows_pass"] is True
    assert summary["claim_boundary_rows_pass"] is True
    assert summary["gate_matrix_pass"] is True
    assert summary["ordinary_success_denominator_allowed"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["success_rate_verdict_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    execution_rows = _read_csv(output_dir / "paired_execution_rows.csv")
    delta_rows = _read_csv(output_dir / "paired_delta_rows.csv")
    surface_delta_rows = _read_csv(output_dir / "surface_delta_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    assert len(execution_rows) == 8
    assert len(delta_rows) == 4
    assert {row["surface_id"] for row in surface_delta_rows} == {"fresh_disjoint", "m2850_explanatory"}
    assert all(row["ranking_admissible"] == "False" for row in delta_rows + surface_delta_rows)
    assert all(row["ordinary_success_denominator_allowed"] == "False" for row in delta_rows + surface_delta_rows)
    assert any(row["claim_id"] == "m2868-claim-follow_up_result_audit_registered" for row in claim_rows)
    assert follow_up.exists()
