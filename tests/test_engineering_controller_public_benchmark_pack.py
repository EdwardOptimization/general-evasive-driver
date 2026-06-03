import csv
import json
from pathlib import Path

from autodrift.engineering_controller_public_benchmark_pack import (
    REQUIRED_FILES,
    materialize_public_benchmark_pack,
)


FALSE_CLAIM_FLAGS = [
    "external_high_fidelity_simulation_included",
    "policy_action_run",
    "policy_rollout_run",
    "measured_validation_run",
    "training_run",
    "replay_run",
    "ppo_run",
    "ranking_run",
    "winner_selected",
    "checkpoint_promoted",
    "success_rate_computed",
    "controller_family_verdict_computed",
    "driver_performance_claim_made",
    "verdict_claim_made",
    "paper_claim_made",
    "finite_window_vs_gru_claim_made",
    "level3_self_id_claim_made",
    "current_sim_verdict_claim_made",
    "high_fidelity_validation_claim_made",
]


def test_materialize_public_benchmark_pack_writes_claim_bounded_files(tmp_path):
    pack_dir = tmp_path / "pack"

    result = materialize_public_benchmark_pack(
        pack_dir,
        milestone="m2505-test",
        next_blocker="m2506-test",
    )

    assert result.summary["status_pass"] is True
    assert (
        result.summary["result_class"]
        == "engineering_controller_public_benchmark_pack_materialization_preflight_pass"
    )
    assert result.summary["artifact_manifest_rows"] >= 13
    assert result.summary["required_files_present"] is True
    assert result.summary["source_artifacts_exist"] is True
    assert result.summary["missing_source_artifacts"] == []
    assert result.summary["actor_contract_shape_72_action_3"] is True
    assert result.summary["claim_boundary_present"] is True
    assert result.summary["known_limitations_present"] is True
    assert result.summary["source_only_diagnostic_scope"] is True

    for file_name in REQUIRED_FILES:
        assert (pack_dir / file_name).exists()

    summary_on_disk = json.loads((pack_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary_on_disk == result.summary
    for flag in FALSE_CLAIM_FLAGS:
        assert result.summary[flag] is False


def test_artifact_manifest_references_existing_source_artifacts(tmp_path):
    pack_dir = tmp_path / "pack"

    materialize_public_benchmark_pack(pack_dir)

    with (pack_dir / "artifact_manifest.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) >= 13
    assert {row["source_exists"] for row in rows} == {"True"}
    assert all(Path(row["path"]).exists() for row in rows)
    assert "docs/post-m2470-route-plan.md" in {row["path"] for row in rows}
    assert {
        "docs/m2503-engineering-controller-source-only-metric-panel-branch-synthesis.md",
        "runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/summary.json",
        "runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/summary.json",
    }.issubset({row["path"] for row in rows})


def test_pack_markdown_rejects_public_overclaims(tmp_path):
    pack_dir = tmp_path / "pack"

    materialize_public_benchmark_pack(pack_dir)

    actor_contract = (pack_dir / "actor_contract.md").read_text(encoding="utf-8")
    claim_boundary = (pack_dir / "claim_boundary.md").read_text(encoding="utf-8")
    readme = (pack_dir / "README.md").read_text(encoding="utf-8")
    scenario_role = (pack_dir / "scenario_role_diagnostics.md").read_text(encoding="utf-8")
    baseline = (pack_dir / "baseline_comparison_diagnostics.md").read_text(encoding="utf-8")

    assert "P0 observation shape: 72" in actor_contract
    assert "action shape: 3" in actor_contract
    assert "actor encoder: `human_view_online_gru`" in actor_contract

    for phrase in [
        "driver performance",
        "success-rate",
        "controller ranking",
        "controller-family ranking",
        "winner selection",
        "high-fidelity validation",
        "paper",
        "finite-window-vs-GRU",
        "level3 self-identification",
    ]:
        assert phrase in claim_boundary

    assert "source-only engineering diagnostic artifact" in readme
    assert "not a driver-performance benchmark" in readme
    assert "telemetry rows / role panel rows: 300 / 3" in scenario_role
    assert "telemetry rows / role-subject panel rows: 900 / 9" in baseline
    assert "do not rank controller" in baseline.lower()
