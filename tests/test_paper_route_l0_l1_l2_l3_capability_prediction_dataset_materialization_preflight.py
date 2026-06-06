import csv
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight import (
    write_preflight_artifacts,
)
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight import REQUIRED_PROFILES


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _candidate(candidate_id: str, task_source_id: str, classification: str, *, artifact_count: int = 2) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "task_source_id": task_source_id,
        "task_family": "T4",
        "source_edge": "actuator_delay_step|capability_step_up",
        "window_tag": "reveal_plus_4",
        "executable_source_family": "capability_step_up",
        "env_template_family": "t4_capability_step_temporal",
        "profile_count": len(REQUIRED_PROFILES),
        "required_profile_count": len(REQUIRED_PROFILES),
        "diagnostic_artifact_tags": "m2877_execution|m2838_selected_candidate",
        "candidate_artifact_count": artifact_count,
        "guard_artifact_count": 1 if classification == "guard" else 0,
        "paired_delta_count": 1,
        "source_family_tag_count": 2 if classification == "usable" else 1,
        "classification": classification,
        "classification_reason": f"{classification} test row",
    }


def _workload_rows(task_source_ids: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for task_source_id in task_source_ids:
        for profile in REQUIRED_PROFILES:
            rows.append(
                {
                    "workload_id": f"{task_source_id}::{profile}",
                    "task_source_id": task_source_id,
                    "profile_name": profile,
                    "task_family": "T4",
                    "source_edge": "actuator_delay_step|capability_step_up",
                    "window_tag": "reveal_plus_4",
                    "executable_source_family": "capability_step_up",
                    "env_template_family": "t4_capability_step_temporal",
                    "strata": "test",
                    "profile_config_path": f"configs/{profile}.json",
                    "checkpoint_path": f"checkpoints/{profile}.pt",
                    "config_exists": "True",
                    "checkpoint_exists": "True",
                    "environment_rollout_scheduled": "False",
                    "training_scheduled": "False",
                    "profile_specific_tuning": "False",
                }
            )
    return rows


def _write_fixture_inputs(tmp_path: Path) -> tuple[Path, Path]:
    m2884_dir = tmp_path / "runs" / "m2884"
    workload = tmp_path / "runs" / "m1690" / "executable_workload_matrix.csv"
    _write_rows(
        m2884_dir / "candidate_panel_rows.csv",
        [
            _candidate("candidate-1", "task-1", "usable"),
            _candidate("candidate-2", "task-2", "usable"),
            _candidate("candidate-3", "task-3", "source-singleton", artifact_count=1),
            _candidate("candidate-4", "task-4", "guard", artifact_count=0),
        ],
    )
    _write_rows(
        m2884_dir / "target_inventory_rows.csv",
        [
            {
                "target_id": "target-1",
                "target_family": "future_yaw_authority",
                "required_columns": "max_abs_yaw_rate",
                "available_columns": "max_abs_yaw_rate",
                "status_pass": "True",
                "actor_visible_allowed": "False",
            }
        ],
    )
    _write_rows(
        m2884_dir / "actor_contract_rows.csv",
        [
            {
                "guard_id": "actor-p0",
                "guard_family": "p0_observation_dim",
                "observed": "72",
                "expected": "72",
                "status_pass": "True",
                "actor_visible_allowed": "False",
            },
            {
                "guard_id": "actor-action",
                "guard_family": "action_dim",
                "observed": "3",
                "expected": "3",
                "status_pass": "True",
                "actor_visible_allowed": "False",
            },
        ],
    )
    (m2884_dir / "summary.json").write_text('{"status_pass": true}\n', encoding="utf-8")
    _write_rows(workload, _workload_rows(["task-1", "task-2"]))
    return m2884_dir, workload


def test_m2887_materializes_actor_safe_dataset_contract(tmp_path):
    m2884_dir, workload = _write_fixture_inputs(tmp_path)
    output_dir = tmp_path / "runs" / "m2887"
    follow_up_manifest = tmp_path / "experiments" / "manifests" / "m2888.json"

    summary = write_preflight_artifacts(
        output_dir=output_dir,
        follow_up_manifest=follow_up_manifest,
        m2884_dir=m2884_dir,
        m1690_workload=workload,
        expected_usable_count=2,
        expected_source_singleton_count=1,
        expected_guard_count=1,
    )

    assert summary["status_pass"] is True
    assert summary["decision"] == "dataset_materialization_complete_route_to_m2888_result_audit"
    assert summary["usable_task_row_count"] == 2
    assert summary["profile_task_row_count"] == 2 * len(REQUIRED_PROFILES)
    assert summary["source_singleton_exclusion_row_count"] == 1
    assert summary["guard_exclusion_row_count"] == 1
    assert summary["evaluator_targets_actor_visible"] is False
    assert summary["hidden_oracle_actor_input_required"] is False
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["source_singleton_rows_paper_proof_allowed"] is False
    assert summary["guard_rows_ordinary_success_denominator_allowed"] is False
    assert summary["false_claim_flags"]["training_run"] is False
    assert summary["false_claim_flags"]["ranking_run"] is False
    assert summary["false_claim_flags"]["driver_performance_claim_made"] is False

    usable_rows = _read_rows(output_dir / "usable_task_rows.csv")
    profile_rows = _read_rows(output_dir / "profile_task_rows.csv")
    evaluator_rows = _read_rows(output_dir / "evaluator_target_rows.csv")
    singleton_rows = _read_rows(output_dir / "excluded_source_singleton_rows.csv")
    guard_rows = _read_rows(output_dir / "excluded_guard_rows.csv")
    gate_rows = _read_rows(output_dir / "dataset_gate_rows.csv")
    claim_rows = _read_rows(output_dir / "claim_rows.csv")

    assert len(usable_rows) == 2
    assert len(profile_rows) == 24
    assert {row["environment_rollout_scheduled"] for row in profile_rows} == {"False"}
    assert {row["training_scheduled"] for row in profile_rows} == {"False"}
    assert {row["actor_visible_target_fields"] for row in profile_rows} == {""}
    assert {row["actor_visible_allowed"] for row in evaluator_rows} == {"False"}
    assert singleton_rows[0]["paper_proof_allowed"] == "False"
    assert singleton_rows[0]["may_seed_future_panel"] == "True"
    assert guard_rows[0]["ordinary_success_denominator_allowed"] == "False"
    assert guard_rows[0]["may_seed_future_panel"] == "False"
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {row["claim_family"] for row in claim_rows if row["claim_allowed"] == "False"}.issuperset(
        {"driver performance", "finite-window-vs-GRU verdict", "level3 self-ID"}
    )
    assert follow_up_manifest.exists()
    assert read_json(follow_up_manifest)["id"].startswith("m2888-")


def test_m2887_reports_incomplete_when_row_count_gate_fails(tmp_path):
    m2884_dir, workload = _write_fixture_inputs(tmp_path)
    output_dir = tmp_path / "runs" / "m2887"

    summary = write_preflight_artifacts(
        output_dir=output_dir,
        follow_up_manifest=tmp_path / "m2888.json",
        m2884_dir=m2884_dir,
        m1690_workload=workload,
        expected_usable_count=3,
        expected_source_singleton_count=1,
        expected_guard_count=1,
    )

    assert summary["status_pass"] is False
    assert summary["decision"] == "dataset_materialization_incomplete_route_to_m2888_result_audit"
    gates = {row["gate_id"]: row for row in _read_rows(output_dir / "dataset_gate_rows.csv")}
    assert gates["m2887-usable-task-row-count"]["status_pass"] == "False"
    assert gates["m2887-usable-task-row-count"]["failure_type"] == "scenario_sampling_failure"
