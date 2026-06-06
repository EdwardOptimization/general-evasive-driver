import csv
from pathlib import Path

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_fitting_implementation_preflight import (
    DEFAULT_SEEDS,
    build_task_source_split_rows,
    write_preflight_artifacts,
)
from autodrift.paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight import REQUIRED_PROFILES


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_fixture(tmp_path: Path, *, task_count: int = 5) -> tuple[Path, Path, Path, Path, Path, Path]:
    m2891_dir = tmp_path / "runs" / "m2891"
    m2893_dir = tmp_path / "runs" / "m2893"
    m2887_dir = tmp_path / "runs" / "m2887"
    m2884_dir = tmp_path / "runs" / "m2884"
    execution_dir = tmp_path / "runs" / "execution"
    for directory in [m2891_dir, m2893_dir, m2887_dir, m2884_dir, execution_dir]:
        directory.mkdir(parents=True)

    label_rows = [
        {
            "label_contract_id": "label-1",
            "target_family": "future_braking_deceleration_envelope",
            "required_columns": "brake_scale|speed_mean",
            "available_columns": "brake_scale|speed_mean",
            "target_visibility": "evaluator_only_actor_invisible",
            "actor_visible_allowed": "False",
            "normalization_policy": "robust_z_score",
            "missing_value_policy": "mask",
            "loss_family": "robust_regression",
            "metric_family": "per_target_mae",
            "status_pass": "True",
            "failure_type": "none",
            "claim_boundary": "fixture",
        },
        {
            "label_contract_id": "label-2",
            "target_family": "recovery_margin_after_maneuver",
            "required_columns": "recoverability_window_success|min_clearance_margin",
            "available_columns": "recoverability_window_success|min_clearance_margin",
            "target_visibility": "evaluator_only_actor_invisible",
            "actor_visible_allowed": "False",
            "normalization_policy": "robust_z_score",
            "missing_value_policy": "mask",
            "loss_family": "robust_regression|binary_recoverability",
            "metric_family": "per_target_mae",
            "status_pass": "True",
            "failure_type": "none",
            "claim_boundary": "fixture",
        },
    ]
    write_csv_rows(m2891_dir / "label_contract_rows.csv", label_rows)
    write_csv_rows(
        m2891_dir / "split_contract_rows.csv",
        [
            {
                "split_contract_id": "split-1",
                "split_unit": "task_source_id",
                "paper_holdout_admitted": "False",
                "preflight_only": "True",
                "status_pass": "True",
            }
        ],
    )
    write_csv_rows(
        m2891_dir / "baseline_contract_rows.csv",
        [
            {
                "baseline_contract_id": f"baseline-{index}",
                "profile_name": profile,
                "profile_level": profile.split("_", 1)[0],
                "profile_task_count": task_count,
                "status_pass": "True",
            }
            for index, profile in enumerate(REQUIRED_PROFILES, start=1)
        ],
    )
    write_json(
        m2891_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "m2887_dir": str(m2887_dir),
            "source_singleton_rows_paper_proof_allowed": False,
            "guard_rows_ordinary_success_denominator_allowed": False,
            "baseline_checkpoints": ["checkpoint.pt"],
        },
    )

    write_json(
        m2893_dir / "summary.json",
        {
            "status_pass": True,
            "gate_matrix_pass": True,
            "baseline_checkpoints": ["checkpoint.pt"],
        },
    )
    write_csv_rows(
        m2893_dir / "loader_smoke_rows.csv",
        [
            {
                "loader_smoke_id": f"loader-{index}",
                "profile_name": profile,
                "profile_level": profile.split("_", 1)[0],
                "status_pass": "True",
            }
            for index, profile in enumerate(REQUIRED_PROFILES, start=1)
        ],
    )
    write_csv_rows(
        m2893_dir / "model_head_smoke_rows.csv",
        [
            {
                "model_head_smoke_id": f"head-{index}",
                "profile_name": profile,
                "profile_level": profile.split("_", 1)[0],
                "input_shape": "batch,obs=72",
                "target_scalar_dim": 4,
                "status_pass": "True",
            }
            for index, profile in enumerate(REQUIRED_PROFILES, start=1)
        ],
    )

    usable_rows = []
    profile_rows = []
    execution_rows = []
    for task_index in range(1, task_count + 1):
        task_source_id = f"task-{task_index:04d}"
        usable_rows.append(
            {
                "materialized_task_id": f"usable-{task_index:04d}",
                "task_source_id": task_source_id,
                "task_family": "T4",
                "profile_count": len(REQUIRED_PROFILES),
                "required_profile_count": len(REQUIRED_PROFILES),
                "diagnostic_artifact_tags": "fixture_execution",
            }
        )
        for profile_index, profile in enumerate(REQUIRED_PROFILES, start=1):
            profile_rows.append(
                {
                    "profile_task_id": f"usable-{task_index:04d}::profile-{profile_index:02d}",
                    "materialized_task_id": f"usable-{task_index:04d}",
                    "task_source_id": task_source_id,
                    "profile_name": profile,
                    "profile_level": profile.split("_", 1)[0],
                    "status_pass": "True",
                }
            )
        execution_rows.append(
            {
                "task_source_id": task_source_id,
                "profile_name": "L3_online_gru",
                "brake_scale": 0.8 + 0.1 * task_index,
                "speed_mean": 6.0 + task_index,
                "recoverability_window_success": str(task_index % 2 == 0),
                "min_clearance_margin": 2.5 + task_index,
            }
        )
    write_csv_rows(m2887_dir / "usable_task_rows.csv", usable_rows)
    write_csv_rows(m2887_dir / "profile_task_rows.csv", profile_rows)
    write_json(m2887_dir / "summary.json", {"status_pass": True, "gate_matrix_pass": True, "m2884_dir": str(m2884_dir)})
    write_csv_rows(execution_dir / "candidate_execution_rows.csv", execution_rows)
    write_csv_rows(
        m2884_dir / "source_inventory_rows.csv",
        [
            {
                "source_inventory_id": "source-1",
                "artifact_tag": "fixture_execution",
                "path": str(execution_dir / "candidate_execution_rows.csv"),
                "path_exists": "True",
            }
        ],
    )

    m2896_design = tmp_path / "docs" / "m2896.md"
    m2897_audit = tmp_path / "docs" / "m2897.md"
    m2896_design.parent.mkdir(parents=True)
    m2896_design.write_text("design\n", encoding="utf-8")
    m2897_audit.write_text("audit\n", encoding="utf-8")
    return m2891_dir, m2893_dir, m2896_design, m2897_audit, tmp_path / "runs" / "m2898", tmp_path / "experiments" / "m2899.json"


def test_m2898_runs_bounded_fitting_preflight_and_writes_required_artifacts(tmp_path):
    m2891_dir, m2893_dir, m2896_design, m2897_audit, output_dir, follow_up = _write_fixture(tmp_path)

    summary = write_preflight_artifacts(
        output_dir=output_dir,
        follow_up_manifest=follow_up,
        m2896_design=m2896_design,
        m2897_audit=m2897_audit,
        m2893_dir=m2893_dir,
        m2891_dir=m2891_dir,
        seed_list=[DEFAULT_SEEDS[0]],
        optimizer_steps=3,
    )

    assert summary["status_pass"] is True
    assert summary["decision"] == "fitting_implementation_preflight_complete_route_to_m2899_result_audit"
    assert summary["optimizer_step_run"] is True
    assert summary["optimizer_step_row_count"] == len(REQUIRED_PROFILES) * 3
    assert summary["fitted_weights_persisted"] is True
    assert summary["fitted_weight_checkpoint_count"] == len(REQUIRED_PROFILES)
    assert summary["training_run"] is False
    assert summary["validation_run"] is False
    assert summary["ranking_run"] is False
    assert summary["model_quality_claim_made"] is False
    assert summary["paper_claim_made"] is False
    assert follow_up.exists()
    assert read_json(follow_up)["id"].startswith("m2899-")

    for artifact_name in [
        "fitting_recipe_rows",
        "task_source_split_rows",
        "target_normalization_rows",
        "availability_mask_rows",
        "optimizer_step_rows",
        "profile_metric_diagnostic_rows",
        "baseline_diagnostic_rows",
        "overfit_guard_rows",
        "rollback_rows",
        "claim_rows",
    ]:
        assert Path(summary["artifacts"][artifact_name]).exists()

    claim_rows = _read_rows(output_dir / "claim_rows.csv")
    rollback_rows = _read_rows(output_dir / "rollback_rows.csv")
    assert {row["claim_family"] for row in claim_rows if row["claim_made"] == "False"}.issuperset(
        {"model_quality", "paper", "finite_window_vs_gru", "level3_self_id"}
    )
    assert {row["status_pass"] for row in rollback_rows} == {"True"}


def test_m2898_task_source_split_has_no_profile_leakage():
    rows = [
        {"materialized_task_id": f"task-{index}", "task_source_id": f"source-{index:04d}", "profile_count": len(REQUIRED_PROFILES)}
        for index in range(1, 6)
    ]

    split_rows = build_task_source_split_rows(rows)

    assert {row["split_unit"] for row in split_rows} == {"task_source_id"}
    assert {row["profile_leakage_detected"] for row in split_rows} == {False}
    assert [row["split_name"] for row in split_rows].count("smoke_eval") == 1
