import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_implementation_preflight import (
    build_schema_rows,
    build_loader_smoke_rows,
    write_preflight_artifacts,
)
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight import REQUIRED_PROFILES


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _feature_rows(*, future_target_input_allowed: bool = False) -> list[dict[str, object]]:
    rows = []
    for index, profile in enumerate(REQUIRED_PROFILES, start=1):
        if profile.startswith("L2_window_") and "current_tiled" not in profile:
            feature_family = "finite_window_command_response_history"
            expected_shape = "obs=72;window=13"
        elif "current_tiled" in profile:
            feature_family = "current_tiled_history_control"
            expected_shape = "obs=72;window=13"
        elif profile.startswith("L3_"):
            feature_family = "recurrent_hidden_state"
            expected_shape = "obs=72;hidden=actor_internal"
        elif profile.startswith("L1_"):
            feature_family = "previous_command_and_actuator_state"
            expected_shape = "obs=72"
        else:
            feature_family = "current_deployable_observation"
            expected_shape = "obs=72"
        rows.append(
            {
                "feature_contract_id": f"feature-{index}",
                "profile_name": profile,
                "profile_level": profile.split("_", 1)[0],
                "feature_family": feature_family,
                "feature_source": "fixture",
                "expected_shape": expected_shape,
                "actor_visible_allowed": "True",
                "hidden_oracle_input_allowed": "False",
                "future_target_input_allowed": str(future_target_input_allowed if index == 1 else False),
                "status_pass": "True",
                "failure_type": "none",
                "claim_boundary": "fixture",
            }
        )
    return rows


def _label_rows() -> list[dict[str, object]]:
    return [
        {
            "label_contract_id": "label-1",
            "target_family": "future_yaw_authority",
            "required_columns": "max_abs_yaw_rate|post_event_yaw_rate_abs|beta_abs_peak",
            "available_columns": "max_abs_yaw_rate|post_event_yaw_rate_abs|beta_abs_peak",
            "target_visibility": "evaluator_only_actor_invisible",
            "actor_visible_allowed": "False",
            "normalization_policy": "robust_z_score",
            "missing_value_policy": "mask",
            "loss_family": "robust_regression",
            "metric_family": "mae",
            "status_pass": "True",
            "failure_type": "none",
            "claim_boundary": "fixture",
        },
        {
            "label_contract_id": "label-2",
            "target_family": "recovery_margin_after_maneuver",
            "required_columns": "recovery_time_proxy|recoverability_window_success",
            "available_columns": "recovery_time_proxy|recoverability_window_success",
            "target_visibility": "evaluator_only_actor_invisible",
            "actor_visible_allowed": "False",
            "normalization_policy": "robust_z_score",
            "missing_value_policy": "mask",
            "loss_family": "robust_regression|binary_recoverability",
            "metric_family": "mae",
            "status_pass": "True",
            "failure_type": "none",
            "claim_boundary": "fixture",
        },
    ]


def _baseline_rows(sample_count: int = 2) -> list[dict[str, object]]:
    return [
        {
            "baseline_contract_id": f"baseline-{index}",
            "comparison_family": "fixture",
            "profile_name": profile,
            "profile_level": profile.split("_", 1)[0],
            "profile_task_count": sample_count,
            "training_scheduled": "False",
            "environment_rollout_scheduled": "False",
            "profile_specific_tuning": "False",
            "status_pass": "True",
            "failure_type": "none",
            "claim_boundary": "fixture",
        }
        for index, profile in enumerate(REQUIRED_PROFILES, start=1)
    ]


def _write_m2891_fixture(tmp_path: Path, *, future_target_input_allowed: bool = False) -> Path:
    m2891_dir = tmp_path / "runs" / "m2891"
    m2891_dir.mkdir(parents=True)
    feature_rows = _feature_rows(future_target_input_allowed=future_target_input_allowed)
    label_rows = _label_rows()
    split_rows = [
        {
            "split_contract_id": "split-1",
            "split_family": "task_source_no_profile_leakage",
            "split_unit": "task_source_id",
            "group_key": "all",
            "task_source_count": 2,
            "profile_task_count": len(REQUIRED_PROFILES) * 2,
            "paper_holdout_admitted": "False",
            "preflight_only": "True",
            "non_leaking_split_possible": "True",
            "status_pass": "True",
            "failure_type": "none",
            "claim_boundary": "fixture",
        }
    ]
    loss_rows = [
        {
            "loss_metric_contract_id": f"loss-{index}",
            "target_family": row["target_family"],
            "loss_family": row["loss_family"],
            "metric_family": row["metric_family"],
            "availability_mask_required": "True",
            "paper_ranking_allowed": "False",
            "status_pass": "True",
            "failure_type": "none",
            "claim_boundary": "fixture",
        }
        for index, row in enumerate(label_rows, start=1)
    ]
    baseline_rows = _baseline_rows()
    gate_rows = [
        {
            "gate_id": "gate-1",
            "gate_family": "fixture",
            "status_pass": "True",
            "observed": "ok",
            "expected": "ok",
            "failure_type": "none",
            "claim_boundary": "fixture",
        }
    ]
    claim_rows = [
        {
            "claim_id": "claim-1",
            "claim_family": "contract materialized",
            "claim_made": "True",
            "claim_allowed": "True",
            "evidence_required_before_claim": "fixture",
            "claim_boundary": "fixture",
        },
        {
            "claim_id": "claim-2",
            "claim_family": "training",
            "claim_made": "False",
            "claim_allowed": "False",
            "evidence_required_before_claim": "separate manifest",
            "claim_boundary": "fixture",
        },
    ]
    write_csv_rows(m2891_dir / "feature_contract_rows.csv", feature_rows)
    write_csv_rows(m2891_dir / "label_contract_rows.csv", label_rows)
    write_csv_rows(m2891_dir / "split_contract_rows.csv", split_rows)
    write_csv_rows(m2891_dir / "loss_metric_contract_rows.csv", loss_rows)
    write_csv_rows(m2891_dir / "baseline_contract_rows.csv", baseline_rows)
    write_csv_rows(m2891_dir / "modeling_gate_rows.csv", gate_rows)
    write_csv_rows(m2891_dir / "claim_rows.csv", claim_rows)
    write_json(
        m2891_dir / "summary.json",
        {
            "status_pass": not future_target_input_allowed,
            "gate_matrix_pass": not future_target_input_allowed,
            "usable_task_row_count": 2,
            "profile_task_row_count": len(REQUIRED_PROFILES) * 2,
            "source_singleton_exclusion_row_count": 1,
            "guard_exclusion_row_count": 1,
            "source_singleton_rows_paper_proof_allowed": False,
            "guard_rows_ordinary_success_denominator_allowed": False,
            "baseline_checkpoints": ["checkpoint.pt"],
        },
    )
    return m2891_dir


def test_m2893_materializes_schema_loader_and_model_head_smoke(tmp_path):
    m2891_dir = _write_m2891_fixture(tmp_path)
    audit = tmp_path / "docs" / "m2892.md"
    audit.parent.mkdir(parents=True)
    audit.write_text("accepted\n", encoding="utf-8")
    output_dir = tmp_path / "runs" / "m2893"
    follow_up_manifest = tmp_path / "experiments" / "manifests" / "m2894.json"

    summary = write_preflight_artifacts(
        output_dir=output_dir,
        follow_up_manifest=follow_up_manifest,
        m2891_dir=m2891_dir,
        m2892_audit=audit,
    )

    assert summary["status_pass"] is True
    assert summary["decision"] == "implementation_preflight_pass_route_to_m2894_result_audit"
    assert summary["feature_schema_row_count"] == len(REQUIRED_PROFILES)
    assert summary["label_schema_row_count"] == 2
    assert summary["loader_smoke_row_count"] == len(REQUIRED_PROFILES)
    assert summary["model_head_smoke_row_count"] == len(REQUIRED_PROFILES)
    assert summary["target_scalar_dim"] == 5
    assert summary["optimizer_step_run"] is False
    assert summary["fitted_weights_persisted"] is False
    assert summary["training_run"] is False
    assert summary["model_quality_claim_made"] is False

    schema_rows = _read_rows(output_dir / "schema_rows.csv")
    loader_rows = _read_rows(output_dir / "loader_smoke_rows.csv")
    model_head_rows = _read_rows(output_dir / "model_head_smoke_rows.csv")
    gate_rows = _read_rows(output_dir / "gate_rows.csv")
    claim_rows = _read_rows(output_dir / "claim_rows.csv")

    assert {row["future_target_input_allowed"] for row in schema_rows if row["schema_family"] == "actor_feature_schema"} == {
        "False"
    }
    assert {row["actor_visible_allowed"] for row in schema_rows if row["schema_family"] == "evaluator_label_schema"} == {
        "False"
    }
    assert {row["optimizer_step_scheduled"] for row in loader_rows} == {"False"}
    assert {row["optimizer_step_run"] for row in model_head_rows} == {"False"}
    assert {row["fitted_weights_persisted"] for row in model_head_rows} == {"False"}
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert {row["claim_family"] for row in claim_rows if row["claim_allowed"] == "False"}.issuperset(
        {"optimizer step", "fitted weights", "model quality", "level3 self-ID"}
    )
    assert follow_up_manifest.exists()
    assert read_json(follow_up_manifest)["id"].startswith("m2894-")


def test_m2893_rejects_future_target_feature_contract():
    schema_rows = build_schema_rows(_feature_rows(future_target_input_allowed=True), _label_rows())
    feature_rows = [row for row in schema_rows if row["schema_family"] == "actor_feature_schema"]

    assert any(row["status_pass"] is False for row in feature_rows)
    assert any(row["failure_type"] == "contract_violation" for row in feature_rows)


def test_m2893_loader_smoke_blocks_paper_holdout():
    feature_rows = _feature_rows()
    label_rows = _label_rows()
    baseline_rows = _baseline_rows()
    split_rows = [
        {
            "paper_holdout_admitted": "True",
            "preflight_only": "False",
        }
    ]

    loader_rows = build_loader_smoke_rows(feature_rows, label_rows, baseline_rows, split_rows)

    assert {row["status_pass"] for row in loader_rows} == {False}
    assert {row["failure_type"] for row in loader_rows} == {"contract_violation"}
