import csv
import json
from pathlib import Path

from autodrift import (
    engineering_controller_route_a_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight
    as m2728,
)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_m2728_executes_candidate_rows_with_temporary_overlay(monkeypatch, tmp_path):
    monkeypatch.setattr(m2728, "EXPECTED_CANDIDATE_COUNT", 2)
    monkeypatch.setattr(m2728, "EXPECTED_OVERLAY_ROW_COUNT", 3)
    monkeypatch.setattr(m2728, "EXPECTED_GUARDRAIL_ROW_COUNT", 1)

    m2725_dir = tmp_path / "m2725"
    output_dir = tmp_path / "m2728"
    specs_path = tmp_path / "specs.json"
    workload_path = tmp_path / "workload.csv"
    design_path = tmp_path / "m2727.md"
    follow_up_manifest = tmp_path / "m2729.json"
    doc_path = tmp_path / "doc.md"

    design_path.write_text(
        "admit_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight",
        encoding="utf-8",
    )
    write_json(follow_up_manifest, {"id": "m2729"})
    write_json(m2725_dir / "summary.json", {"status_pass": True})

    candidate_rows = []
    workload_rows = []
    specs = []
    for index in range(2):
        task_id = f"task-{index}"
        profile_name = f"profile-{index}"
        workload_id = f"{task_id}::{profile_name}"
        config_path = tmp_path / f"{profile_name}.json"
        checkpoint_path = tmp_path / f"{profile_name}.pt"
        write_json(config_path, {"env": {"history_length": 4}})
        checkpoint_path.write_text("checkpoint", encoding="utf-8")
        specs.append(
            {
                "task_source_id": task_id,
                "env_config": {
                    "history_length": 4,
                    "track_cost_scale": 1.0,
                    "track_width": 8.0,
                    "obstacle": {
                        "collision_penalty": 1.0,
                        "distance_range": [10.0, 15.0],
                        "half_width_range": [1.0, 2.0],
                    },
                },
            }
        )
        candidate_rows.append(
            {
                "candidate_row_id": f"candidate-{index}",
                "source_panel_row_id": f"panel-{index}",
                "source_candidate_id": f"source-{index}",
                "anchor_task_source_id": f"anchor-{index}",
                "workload_id": workload_id,
                "task_source_id": task_id,
                "profile_name": profile_name,
                "task_family": "T4",
                "target_family": "offtrack_repair_target",
                "repair_overlay_id": "m2725-shared-road-containment-overlay",
                "guardrail_overlay_id": "m2725-shared-collision-clearance-guardrail",
                "target_accounted": True,
                "active_config_overwritten": False,
                "actor_input_change": False,
                "hidden_oracle_feature_injection": False,
                "target_labels_actor_visible": False,
                "profile_specific_tuning": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "claim_boundary": "test",
            }
        )
        workload_rows.append(
            {
                "workload_id": workload_id,
                "task_source_id": task_id,
                "profile_name": profile_name,
                "task_family": "T4",
                "source_edge": "edge",
                "window_tag": "window",
                "executable_source_family": "source",
                "env_template_family": "template",
                "strata": "strata",
                "profile_config_path": str(config_path),
                "checkpoint_path": str(checkpoint_path),
                "config_exists": True,
                "checkpoint_exists": True,
                "environment_rollout_scheduled": False,
                "training_scheduled": False,
                "profile_specific_tuning": False,
            }
        )

    write_json(specs_path, {"executable_task_specs": specs})
    write_csv(workload_path, workload_rows)
    write_csv(m2725_dir / "candidate_target_rows.csv", candidate_rows)
    write_csv(
        m2725_dir / "shared_repair_overlay_rows.csv",
        [
            {
                "overlay_row_id": "overlay-1",
                "overlay_id": "m2725-shared-road_containment-overlay",
                "overlay_family": "road_containment",
                "target_namespace": "env",
                "target_key": "track_cost_scale",
                "proposed_value": "2.8",
                "preserves_parent_geometry": True,
                "active_config_overwritten": False,
                "actor_input_change": False,
                "hidden_oracle_feature_injection": False,
                "profile_specific_tuning": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "claim_boundary": "test",
            },
            {
                "overlay_row_id": "overlay-2",
                "overlay_id": "m2725-shared-collision_clearance_guardrail-overlay",
                "overlay_family": "collision_clearance_guardrail",
                "target_namespace": "env.obstacle",
                "target_key": "collision_penalty",
                "proposed_value": "25.0",
                "preserves_parent_geometry": True,
                "active_config_overwritten": False,
                "actor_input_change": False,
                "hidden_oracle_feature_injection": False,
                "profile_specific_tuning": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "claim_boundary": "test",
            },
            {
                "overlay_row_id": "overlay-3",
                "overlay_id": "m2725-shared-geometry_guardrail-overlay",
                "overlay_family": "geometry_guardrail",
                "target_namespace": "env",
                "target_key": "track_width",
                "proposed_value": "preserve_parent_value",
                "preserves_parent_geometry": True,
                "active_config_overwritten": False,
                "actor_input_change": False,
                "hidden_oracle_feature_injection": False,
                "profile_specific_tuning": False,
                "repair_execution_started": False,
                "training_started": False,
                "ranking_admissible": False,
                "winner_selected": False,
                "claim_boundary": "test",
            },
        ],
    )
    write_csv(
        m2725_dir / "guardrail_rows.csv",
        [
            {
                "guardrail_row_id": "guardrail-1",
                "guardrail_family": "collision_caution_guardrail",
                "source_panel_row_id": "panel-g",
                "source_candidate_id": "source-g",
                "profile_name": "profile-0",
                "task_family": "T4",
                "taxonomy_family": "obstacle_collision",
                "target_panel_admitted": False,
                "execution_scheduled": False,
                "protected_rows_in_success_denominator": False,
                "diagnostic_only_no_verdict": True,
                "actor_input_change": False,
                "hidden_oracle_feature_injection": False,
                "claim_boundary": "test",
            }
        ],
    )
    write_csv(
        m2725_dir / "actor_contract_rows.csv",
        [{"contract_row_id": "actor", "contract_field": "observation_shape", "observed_value": 72, "expected_value": 72, "status_pass": True, "actor_visible": False, "claim_boundary": "test"}],
    )
    write_csv(
        m2725_dir / "claim_boundary_rows.csv",
        [{"claim_id": "claim", "claim_family": "artifact", "allowed_in_m2725": True, "claim_made": True, "status_pass": True, "evidence_required_before_claim": "test", "claim_boundary": "test"}],
    )
    write_csv(
        m2725_dir / "gate_matrix.csv",
        [{"gate_id": "gate", "gate_family": "artifact", "status_pass": True, "observed": "x", "expected": "x", "failure_type": "", "claim_boundary": "test"}],
    )

    monkeypatch.setattr(m2728, "load_actor_critic_checkpoint", lambda *args, **kwargs: (object(), {}))

    def fake_run_workload_cell(*, workload_row, executable_spec, profile_config, model, profile_row, eval_seed):
        assert executable_spec["env_config"]["track_cost_scale"] == 2.8
        assert executable_spec["env_config"]["obstacle"]["collision_penalty"] == 25.0
        assert executable_spec["env_config"]["track_width"] == 8.0
        return {
            "workload_id": workload_row["workload_id"],
            "task_source_id": workload_row["task_source_id"],
            "profile_name": workload_row["profile_name"],
            "task_family": workload_row["task_family"],
            "source_edge": workload_row["source_edge"],
            "window_tag": workload_row["window_tag"],
            "success": False,
            "collision": False,
            "termination_reason": "off_track",
            "min_clearance_margin": 1.5,
            "return": 2.0,
            "steps": 10,
            "action_rate_mean": 0.1,
            "high_sideslip_fraction": 0.0,
            "eval_seed": eval_seed,
        }

    monkeypatch.setattr(m2728, "run_workload_cell", fake_run_workload_cell)

    summary = m2728.run_current_m1690_exact_executable_reentry_offtrack_repair_bounded_execution_preflight(
        m2725_dir=m2725_dir,
        m2727_design=design_path,
        executable_specs=specs_path,
        executable_workload=workload_path,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
        resume=False,
    )

    assert summary["status_pass"] is True
    assert summary["repair_execution_row_count"] == 2
    assert summary["candidate_execution_failure_row_count"] == 0
    assert summary["repair_overlay_application_row_count"] == 6
    assert summary["guardrail_audit_row_count"] == 1
    assert summary["active_config_overwritten"] is False
    assert summary["gate_matrix_pass"] is True
    snapshot = json.loads((output_dir / "config_snapshots" / "candidate-0.json").read_text(encoding="utf-8"))
    assert snapshot["env_config"]["track_cost_scale"] == 2.8
    assert snapshot["env_config"]["obstacle"]["collision_penalty"] == 25.0
    assert snapshot["env_config"]["track_width"] == 8.0
