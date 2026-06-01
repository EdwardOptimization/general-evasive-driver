from __future__ import annotations

import csv
from pathlib import Path

from autodrift.artifacts import read_json
from autodrift.paper_route_outcome_supported_decisive_comparison_support_candidates import (
    generate_comparison_support_candidates,
)
from autodrift.paper_route_outcome_supported_decisive_comparison_support_materialization_preflight import (
    PROFILE_SUBSET,
    proxy_template_for_candidate,
    run_materialization_preflight,
)


def _profile_tree(root: Path) -> None:
    for profile_name in PROFILE_SUBSET:
        config_path = root / "configs" / f"{profile_name}_seed167400.json"
        checkpoint_path = root / "profile_runs" / profile_name / "seed_167400" / "checkpoint.pt"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("{}", encoding="utf-8")
        checkpoint_path.write_text("checkpoint", encoding="utf-8")


def test_comparison_support_materialization_preflight_writes_expected_artifacts(tmp_path: Path) -> None:
    candidates_path = tmp_path / "candidates.json"
    profile_run_dir = tmp_path / "profiles"
    output_dir = tmp_path / "out"
    generate_comparison_support_candidates(output_path=candidates_path)
    _profile_tree(profile_run_dir)

    summary = run_materialization_preflight(
        candidates_path=candidates_path,
        profile_run_dir=profile_run_dir,
        output_dir=output_dir,
        next_blocker="next-audit",
    )

    assert summary["result_class"] == "comparison_support_materialization_preflight_pass"
    assert summary["candidate_count"] == 240
    assert summary["executable_spec_count"] == 240
    assert summary["workload_row_count"] == 240 * len(PROFILE_SUBSET)
    assert summary["profile_count"] == len(PROFILE_SUBSET)
    assert summary["materialization_failure_count"] == 0
    assert summary["missing_profile_artifact_count"] == 0
    assert summary["contract_violation_count"] == 0
    assert summary["paper_validity_claim_true_count"] == 0
    assert summary["profile_specific_tuning_true_count"] == 0
    assert summary["guardrail_violation_count"] == 0
    assert summary["environment_reset_started"] is False
    assert summary["environment_rollout_started"] is False
    assert summary["policy_action_executed"] is False
    assert summary["paper_level_claim_made"] is False
    assert summary["level3_self_id_claim_made"] is False

    persisted = read_json(output_dir / "summary.json")
    assert persisted["next_blocker"] == "next-audit"
    assert (output_dir / "executable_task_specs.json").exists()
    assert (output_dir / "planned_workload.csv").exists()
    assert (output_dir / "claim_boundary.csv").exists()

    spec_payload = read_json(output_dir / "executable_task_specs.json")
    assert len(spec_payload["executable_task_specs"]) == 240
    assert {row["paper_validity_claim"] for row in spec_payload["executable_task_specs"]} == {False}
    assert {row["profile_specific_tuning"] for row in spec_payload["executable_task_specs"]} == {False}


def test_comparison_support_workload_preserves_claim_guards(tmp_path: Path) -> None:
    candidates_path = tmp_path / "candidates.json"
    profile_run_dir = tmp_path / "profiles"
    output_dir = tmp_path / "out"
    generate_comparison_support_candidates(output_path=candidates_path)
    _profile_tree(profile_run_dir)

    run_materialization_preflight(
        candidates_path=candidates_path,
        profile_run_dir=profile_run_dir,
        output_dir=output_dir,
    )

    with (output_dir / "planned_workload.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert {row["profile_name"] for row in rows} == set(PROFILE_SUBSET)
    assert {row["paper_validity_claim"] for row in rows} == {"False"}
    assert {row["profile_specific_tuning"] for row in rows} == {"False"}
    assert {row["controller_family_ranking_claim_made"] for row in rows} == {"False"}
    assert {row["finite_window_vs_gru_conclusion_made"] for row in rows} == {"False"}
    assert {row["paper_level_claim_made"] for row in rows} == {"False"}
    assert {row["level3_self_id_claim_made"] for row in rows} == {"False"}
    assert {row["materialization_semantics"] for row in rows} == {"comparison_support_smoke_proxy"}


def test_comparison_support_proxy_template_mapping() -> None:
    assert (
        proxy_template_for_candidate(
            {
                "comparison_support_intent": "support_ladder_easy",
                "source_kind": "gentle_yaw_authority_probe",
            }
        )
        == "t4_staged_warmup_capability"
    )
    assert (
        proxy_template_for_candidate(
            {
                "comparison_support_intent": "discriminative_boundary",
                "source_kind": "actuator_delay_discriminative_boundary",
            }
        )
        == "t4_actuator_delay_response"
    )
    assert (
        proxy_template_for_candidate(
            {
                "comparison_support_intent": "collision_relief_probe",
                "source_kind": "near_zero_margin_collision_relief",
            }
        )
        == "t5_boundary_axis_retarget"
    )
