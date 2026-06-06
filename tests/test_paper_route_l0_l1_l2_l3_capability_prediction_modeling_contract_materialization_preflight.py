import csv
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight import (
    write_preflight_artifacts as write_m2887_preflight_artifacts,
)
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_modeling_contract_materialization_preflight import (
    build_label_contract_rows,
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


def _candidate(candidate_id: str, task_source_id: str, classification: str, *, env_template: str) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "task_source_id": task_source_id,
        "task_family": "T4",
        "source_edge": "actuator_delay_step|capability_step_up",
        "window_tag": "reveal_plus_4",
        "executable_source_family": "capability_step_up",
        "env_template_family": env_template,
        "profile_count": len(REQUIRED_PROFILES),
        "required_profile_count": len(REQUIRED_PROFILES),
        "diagnostic_artifact_tags": "m2877_execution|m2838_selected_candidate",
        "candidate_artifact_count": 2,
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


def _write_m2887_fixture(tmp_path: Path) -> Path:
    m2884_dir = tmp_path / "runs" / "m2884"
    workload = tmp_path / "runs" / "m1690" / "executable_workload_matrix.csv"
    _write_rows(
        m2884_dir / "candidate_panel_rows.csv",
        [
            _candidate("candidate-1", "task-1", "usable", env_template="t4_capability_step_temporal"),
            _candidate("candidate-2", "task-2", "usable", env_template="t4_capability_step_temporal"),
            _candidate("candidate-3", "task-3", "source-singleton", env_template="t4_capability_step_temporal"),
            _candidate("candidate-4", "task-4", "guard", env_template="t4_capability_step_temporal"),
        ],
    )
    _write_rows(
        m2884_dir / "target_inventory_rows.csv",
        [
            {
                "target_id": "target-1",
                "target_family": "future_yaw_authority",
                "required_columns": "max_abs_yaw_rate|post_event_yaw_rate_abs",
                "available_columns": "max_abs_yaw_rate|post_event_yaw_rate_abs",
                "status_pass": "True",
                "actor_visible_allowed": "False",
            },
            {
                "target_id": "target-2",
                "target_family": "recovery_margin_after_maneuver",
                "required_columns": "recovery_time_proxy|recoverability_window_success",
                "available_columns": "recovery_time_proxy|recoverability_window_success",
                "status_pass": "True",
                "actor_visible_allowed": "False",
            },
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
            {
                "guard_id": "actor-future-targets",
                "guard_family": "evaluator_targets_actor_visible",
                "observed": "False",
                "expected": "False",
                "status_pass": "True",
                "actor_visible_allowed": "False",
            },
        ],
    )
    (m2884_dir / "summary.json").write_text('{"status_pass": true}\n', encoding="utf-8")
    _write_rows(workload, _workload_rows(["task-1", "task-2"]))
    output_dir = tmp_path / "runs" / "m2887"
    write_m2887_preflight_artifacts(
        output_dir=output_dir,
        follow_up_manifest=tmp_path / "experiments" / "manifests" / "m2888.json",
        m2884_dir=m2884_dir,
        m1690_workload=workload,
        expected_usable_count=2,
        expected_source_singleton_count=1,
        expected_guard_count=1,
    )
    return output_dir


def test_m2891_materializes_actor_safe_modeling_contract(tmp_path):
    m2887_dir = _write_m2887_fixture(tmp_path)
    output_dir = tmp_path / "runs" / "m2891"
    follow_up_manifest = tmp_path / "experiments" / "manifests" / "m2892.json"
    design = tmp_path / "docs" / "m2890.md"
    design.parent.mkdir(parents=True, exist_ok=True)
    design.write_text("design\n", encoding="utf-8")

    summary = write_preflight_artifacts(
        output_dir=output_dir,
        follow_up_manifest=follow_up_manifest,
        m2887_dir=m2887_dir,
        m2890_design=design,
    )

    assert summary["status_pass"] is True
    assert summary["decision"] == "modeling_contract_materialized_route_to_m2892_result_audit"
    assert summary["feature_contract_row_count"] == len(REQUIRED_PROFILES)
    assert summary["label_contract_row_count"] == 2
    assert summary["baseline_contract_row_count"] == len(REQUIRED_PROFILES)
    assert summary["hidden_oracle_actor_input_required"] is False
    assert summary["future_target_actor_input_required"] is False
    assert summary["evaluator_targets_actor_visible"] is False
    assert summary["paper_holdout_admitted"] is False
    assert summary["false_claim_flags"]["model_fitting_run"] is False
    assert summary["false_claim_flags"]["training_run"] is False

    feature_rows = _read_rows(output_dir / "feature_contract_rows.csv")
    label_rows = _read_rows(output_dir / "label_contract_rows.csv")
    split_rows = _read_rows(output_dir / "split_contract_rows.csv")
    baseline_rows = _read_rows(output_dir / "baseline_contract_rows.csv")
    gate_rows = _read_rows(output_dir / "modeling_gate_rows.csv")
    claim_rows = _read_rows(output_dir / "claim_rows.csv")

    assert {row["hidden_oracle_input_allowed"] for row in feature_rows} == {"False"}
    assert {row["future_target_input_allowed"] for row in feature_rows} == {"False"}
    assert {row["actor_visible_allowed"] for row in label_rows} == {"False"}
    assert {row["paper_holdout_admitted"] for row in split_rows} == {"False"}
    assert {row["training_scheduled"] for row in baseline_rows} == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {row["claim_family"] for row in claim_rows if row["claim_allowed"] == "False"}.issuperset(
        {"model fitting", "training", "finite-window-vs-GRU verdict", "level3 self-ID"}
    )
    assert follow_up_manifest.exists()
    assert read_json(follow_up_manifest)["id"].startswith("m2892-")


def test_m2891_rejects_actor_visible_label_contract():
    rows = build_label_contract_rows(
        [
            {
                "target_family": "future_yaw_authority",
                "required_columns": "max_abs_yaw_rate",
                "available_columns": "max_abs_yaw_rate",
                "status_pass": "True",
                "actor_visible_allowed": "True",
                "target_visibility": "evaluator_only_actor_invisible",
            }
        ]
    )

    assert rows[0]["status_pass"] is False
    assert rows[0]["failure_type"] == "contract_violation"
