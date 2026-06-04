from __future__ import annotations

import csv
from pathlib import Path

from autodrift import (
    engineering_controller_route_a_current_m1690_exact_executable_reentry_panel_materialization as m2714,
)
from autodrift.artifacts import read_json, write_csv_rows, write_json


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_m1690_workload(path: Path, *, missing_profile: str | None = None) -> None:
    rows = []
    for task_index in range(1, 10):
        task_source_id = f"m1680-spec-{task_index:04d}"
        for profile in m2714.SELECTED_PROFILES:
            if task_index == 1 and profile == missing_profile:
                continue
            rows.append(
                {
                    "workload_id": f"{task_source_id}::{profile}",
                    "task_source_id": task_source_id,
                    "profile_name": profile,
                    "task_family": "T4" if task_index <= 5 else "T5",
                    "source_edge": f"source-edge-{task_index}",
                    "window_tag": "reveal_plus_4",
                    "executable_source_family": "capability_step_up",
                    "env_template_family": "t4_capability_step_temporal",
                    "strata": "all_72_specs",
                    "profile_config_path": f"configs/{profile}.json",
                    "checkpoint_path": f"checkpoints/{profile}.pt",
                    "config_exists": True,
                    "checkpoint_exists": True,
                    "environment_rollout_scheduled": False,
                    "training_scheduled": False,
                    "profile_specific_tuning": False,
                }
            )
    write_csv_rows(path, rows)


def _write_m2693_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "target_execution_row_count": 9,
            "protected_target_count": 10,
            "protected_target_non_executable_count": 10,
        },
    )
    write_csv_rows(
        root / "target_execution_rows.csv",
        [
            {
                "workload_id": f"m1680-spec-{task_index:04d}::L3_online_gru",
                "task_source_id": f"m1680-spec-{task_index:04d}",
                "profile_name": "L3_online_gru",
                "task_family": "T4" if task_index <= 5 else "T5",
                "source_edge": f"source-edge-{task_index}",
                "window_tag": "reveal_plus_4",
                "termination_reason": "off_track" if task_index != 3 else "speed_too_low",
                "success": False,
                "target_family": "current_sim_offtrack_containment",
            }
            for task_index in range(1, 10)
        ],
    )


def _write_m2710_source(root: Path) -> None:
    root.mkdir()
    write_json(
        root / "summary.json",
        {
            "status_pass": True,
            "workload_fixture_proposal_row_count": 12,
            "proposed_new_current_m1690_workload_row_count": 12,
            "ready_existing_current_m1690_workload_row_count": 0,
            "existing_exact_m1690_match_count": 0,
            "fabricated_existing_m1690_match_count": 0,
            "execution_admitted_row_count": 0,
            "protected_rows_in_success_denominator": False,
        },
    )
    write_csv_rows(
        root / "protected_workload_fixture_proposal_rows.csv",
        [
            {
                "workload_fixture_proposal_id": f"m2710-workload-fixture-proposal-{index:04d}",
                "support_candidate_id": f"m2706-support-candidate-{index:04d}",
                "proposed_workload_id": f"m2710-proposed-{index:04d}::L3_online_gru",
                "profile_name": "L3_online_gru",
                "protected_task_family": "route_a_protected",
                "protected_source_edge": f"unavoidable_mitigation|case-{index}",
                "workload_fixture_support_status": m2714.M2710_PROPOSED_NEW_STATUS,
                "exact_existing_m1690_match": False,
                "protected_rows_in_success_denominator": False,
                "target_labels_actor_visible": False,
                "protected_labels_actor_visible": False,
                "hidden_oracle_actor_input_required": False,
            }
            for index in range(1, 13)
        ],
    )
    write_csv_rows(
        root / "exact_match_admission_rows.csv",
        [
            {
                "admission_id": f"m2710-exact-match-admission-{index:04d}",
                "workload_fixture_proposal_id": f"m2710-workload-fixture-proposal-{index:04d}",
                "support_candidate_id": f"m2706-support-candidate-{index:04d}",
                "exact_match_status": m2714.M2710_EXACT_ABSENT_STATUS,
                "admission_status": m2714.M2710_PROPOSED_NEW_STATUS,
                "execution_admitted": False,
            }
            for index in range(1, 13)
        ],
    )
    write_csv_rows(
        root / "workload_fixture_support_blocker_rows.csv",
        [
            {
                "blocker_id": f"m2710-workload-fixture-blocker-{index:04d}",
                "workload_fixture_proposal_id": f"m2710-workload-fixture-proposal-{index:04d}",
                "support_candidate_id": f"m2706-support-candidate-{index:04d}",
                "blocker_type": m2714.M2710_BLOCKER_ABSENT_STATUS,
            }
            for index in range(1, 13)
        ],
    )


def _write_text_sources(
    *,
    m2712_synthesis: Path,
    m2713_design: Path,
    m2638_blocker: Path,
    route_plan: Path,
    follow_up_manifest: Path,
) -> None:
    m2712_synthesis.write_text("route to m2713 and m2714 exact executable materialization\n", encoding="utf-8")
    m2713_design.write_text(
        "admit_current_m1690_exact_executable_reentry_panel_materialization_preflight\n",
        encoding="utf-8",
    )
    m2638_blocker.write_text("HF3 selected-platform execution is paused until dependency source is supplied\n", encoding="utf-8")
    route_plan.write_text("# Route\n\n## Route A: Engineering Controller Mainline\n", encoding="utf-8")
    write_json(follow_up_manifest, {"id": m2714.DEFAULT_NEXT_BLOCKER})


def test_m2714_materializes_exact_executable_reentry_panel_without_execution(tmp_path: Path) -> None:
    m1690_workload = tmp_path / "executable_workload_matrix.csv"
    m2693_dir = tmp_path / "m2693"
    m2710_dir = tmp_path / "m2710"
    output_dir = tmp_path / "out"
    doc_path = tmp_path / "m2714.md"
    m2712_synthesis = tmp_path / "m2712.md"
    m2713_design = tmp_path / "m2713.md"
    m2638_blocker = tmp_path / "m2638.md"
    route_plan = tmp_path / "route.md"
    follow_up_manifest = tmp_path / "m2715.json"

    _write_m1690_workload(m1690_workload)
    _write_m2693_source(m2693_dir)
    _write_m2710_source(m2710_dir)
    _write_text_sources(
        m2712_synthesis=m2712_synthesis,
        m2713_design=m2713_design,
        m2638_blocker=m2638_blocker,
        route_plan=route_plan,
        follow_up_manifest=follow_up_manifest,
    )

    summary = m2714.materialize_current_m1690_exact_executable_reentry_panel(
        m1690_workload=m1690_workload,
        m2693_dir=m2693_dir,
        m2710_dir=m2710_dir,
        m2712_synthesis=m2712_synthesis,
        m2713_design=m2713_design,
        m2638_blocker=m2638_blocker,
        route_plan=route_plan,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_current_m1690_exact_executable_reentry_panel_materialization_pass"
    )
    assert summary["input_source_row_count"] >= 8
    assert summary["m2693_anchor_task_source_id_count"] == 9
    assert summary["selected_profile_count"] == 4
    assert summary["exact_executable_candidate_row_count"] == 36
    assert summary["profile_context_row_count"] == 36
    assert summary["candidate_rows_all_existing_m1690"] is True
    assert summary["missing_selected_profile_row_count"] == 0
    assert summary["candidate_workload_id_unique_count"] == 36
    assert summary["m2710_protected_proposal_exclusion_row_count"] == 12
    assert summary["protected_execution_admitted_row_count"] == 0
    assert summary["ready_existing_current_m1690_workload_row_count"] == 0
    assert summary["existing_exact_m1690_match_count"] == 0
    assert summary["fabricated_existing_m1690_match_count"] == 0
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_oracle_actor_input_detected"] is False
    assert summary["protected_rows_in_success_denominator"] is False
    assert summary["execution_run"] is False
    assert summary["validation_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["driver_performance_claim_made"] is False
    assert read_json(output_dir / "summary.json") == summary

    source_rows = _read_csv(output_dir / "input_source_rows.csv")
    candidate_rows = _read_csv(output_dir / "exact_executable_candidate_rows.csv")
    profile_rows = _read_csv(output_dir / "profile_context_rows.csv")
    exclusion_rows = _read_csv(output_dir / "protected_proposal_exclusion_rows.csv")
    hf3_rows = _read_csv(output_dir / "hf3_dependency_blocker_rows.csv")
    actor_rows = _read_csv(output_dir / "actor_contract_guard_rows.csv")
    claim_rows = _read_csv(output_dir / "claim_boundary_rows.csv")
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")

    assert {row["source_exists"] for row in source_rows} == {"True"}
    assert {row["profile_name"] for row in candidate_rows} == set(m2714.SELECTED_PROFILES)
    assert {row["exact_executable_reentry_status"] for row in candidate_rows} == {
        m2714.ADMITTED_EXISTING_STATUS
    }
    assert {row["existing_m1690_workload_id_source_backed"] for row in candidate_rows} == {"True"}
    assert {row["execution_run"] for row in candidate_rows + profile_rows} == {"False"}
    assert {row["materialization_only_no_execution"] for row in candidate_rows + profile_rows} == {"True"}
    assert {row["comparison_or_ranking_claim_allowed"] for row in profile_rows} == {"False"}
    assert {row["finite_window_vs_gru_claim_allowed"] for row in profile_rows} == {"False"}
    assert {row["workload_fixture_support_status"] for row in exclusion_rows} == {
        m2714.M2710_PROPOSED_NEW_STATUS
    }
    assert {row["exact_match_status"] for row in exclusion_rows} == {m2714.M2710_EXACT_ABSENT_STATUS}
    assert {row["blocker_type"] for row in exclusion_rows} == {m2714.M2710_BLOCKER_ABSENT_STATUS}
    assert {row["execution_admitted"] for row in exclusion_rows} == {"False"}
    assert {row["protected_rows_in_success_denominator"] for row in exclusion_rows} == {"False"}
    assert {row["exclusion_status"] for row in exclusion_rows} == {m2714.PROTECTED_EXCLUSION_STATUS}
    assert {row["exclusion_status"] for row in hf3_rows} == {m2714.HF3_EXCLUSION_STATUS}
    assert {row["status_pass"] for row in actor_rows} == {"True"}
    assert len(claim_rows) >= 24
    assert {
        row["allowed_in_m2714"]
        for row in claim_rows
        if row["claim_family"] in {"driver_performance", "paper_evidence", "current_sim_verdict"}
    } == {"False"}
    assert len(gate_rows) >= 18
    assert {row["status_pass"] for row in gate_rows} == {"True"}
    assert doc_path.read_text(encoding="utf-8").strip()


def test_m2714_fails_when_selected_profile_row_is_missing(tmp_path: Path) -> None:
    m1690_workload = tmp_path / "executable_workload_matrix.csv"
    m2693_dir = tmp_path / "m2693"
    m2710_dir = tmp_path / "m2710"
    output_dir = tmp_path / "out"
    doc_path = tmp_path / "m2714.md"
    m2712_synthesis = tmp_path / "m2712.md"
    m2713_design = tmp_path / "m2713.md"
    m2638_blocker = tmp_path / "m2638.md"
    route_plan = tmp_path / "route.md"
    follow_up_manifest = tmp_path / "m2715.json"

    _write_m1690_workload(m1690_workload, missing_profile="L2_window_50_current_tiled")
    _write_m2693_source(m2693_dir)
    _write_m2710_source(m2710_dir)
    _write_text_sources(
        m2712_synthesis=m2712_synthesis,
        m2713_design=m2713_design,
        m2638_blocker=m2638_blocker,
        route_plan=route_plan,
        follow_up_manifest=follow_up_manifest,
    )

    summary = m2714.materialize_current_m1690_exact_executable_reentry_panel(
        m1690_workload=m1690_workload,
        m2693_dir=m2693_dir,
        m2710_dir=m2710_dir,
        m2712_synthesis=m2712_synthesis,
        m2713_design=m2713_design,
        m2638_blocker=m2638_blocker,
        route_plan=route_plan,
        output_dir=output_dir,
        doc_path=doc_path,
        follow_up_manifest=follow_up_manifest,
    )

    assert summary["status_pass"] is False
    assert summary["candidate_rows_all_existing_m1690"] is False
    assert summary["missing_selected_profile_row_count"] == 1
    candidate_rows = _read_csv(output_dir / "exact_executable_candidate_rows.csv")
    assert m2714.MISSING_WORKLOAD_STATUS in {row["exact_executable_reentry_status"] for row in candidate_rows}
    gate_rows = _read_csv(output_dir / "gate_matrix.csv")
    failed_gate_names = {row["expected"] for row in gate_rows if row["status_pass"] == "False"}
    assert 0 in {int(value) for value in failed_gate_names if str(value).isdigit()}
