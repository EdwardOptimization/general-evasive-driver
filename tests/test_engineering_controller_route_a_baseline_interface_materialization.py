import csv
import json
from pathlib import Path

from autodrift.engineering_controller_route_a_baseline_interface_materialization import (
    run_route_a_baseline_interface_materialization,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_route_a_baseline_interface_materialization_writes_contract_bound_artifacts(tmp_path):
    output_dir = tmp_path / "run"

    summary = run_route_a_baseline_interface_materialization(output_dir)

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_route_a_baseline_interface_materialization_pass"
    )
    assert summary["required_artifacts_present"] is True
    assert summary["baseline_checkpoint_count"] == 3
    assert summary["all_baseline_checkpoints_exist"] is True
    assert summary["all_baseline_checkpoints_admitted"] is True
    assert summary["all_artifact_sources_exist"] is True
    assert summary["hf0_sources_exist"] is True
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["hidden_or_oracle_actor_inputs_required"] is False
    assert summary["external_high_fidelity_simulation_included"] is False
    assert summary["high_fidelity_simulation_run"] is False
    assert summary["policy_action_run"] is False
    assert summary["training_run"] is False
    assert summary["ranking_run"] is False
    assert summary["winner_selected"] is False
    assert summary["checkpoint_promoted"] is False
    assert summary["success_rate_computed"] is False
    assert summary["driver_performance_claim_made"] is False
    assert summary["m2537_status_pass"] is True
    assert summary["m2537_protected_proof_gates_all_passed"] is False

    baseline_rows = _read_csv(output_dir / "baseline_checkpoint_list.csv")
    artifact_rows = _read_csv(output_dir / "route_a_artifact_map.csv")
    failure_rows = _read_csv(output_dir / "known_failure_taxonomy_extension.csv")
    scenario_rows = _read_csv(output_dir / "scenario_role_metric_report_plan.csv")
    hf0_rows = _read_csv(output_dir / "hf0_interface_boundary_map.csv")
    contract_snapshot = json.loads((output_dir / "actor_io_contract_snapshot.json").read_text())

    assert {row["checkpoint_id"] for row in baseline_rows} == {
        "m1154_original",
        "m2532_guarded_repair",
        "m2537_mitigation_preserving_repair",
    }
    assert {row["checkpoint_admitted"] for row in baseline_rows} == {"True"}
    assert {row["observation_shape"] for row in baseline_rows} == {str(P0_OBSERVATION_DIM)}
    assert {row["action_shape"] for row in baseline_rows} == {str(ACTION_DIM)}
    assert {row["promotion_status"] for row in baseline_rows} >= {"not_promoted"}
    assert {row["source_exists"] for row in baseline_rows} == {"True"}

    assert len(artifact_rows) >= 8
    assert {row["source_exists"] for row in artifact_rows} == {"True"}
    assert {row["failure_id"] for row in failure_rows} == {
        "public_protected_row_overfit_risk",
        "repeated_mitigation_proof_failure",
    }
    assert {
        "stable_aes",
        "drift_required_recovery",
        "unavoidable_mitigation",
        "hidden_dynamics_robustness",
    }.issubset({row["scenario_role"] for row in scenario_rows})
    assert "ActorView" in {row["interface_component"] for row in hf0_rows}
    assert "DIAGNOSTIC_ONLY_KEYS" in {row["interface_component"] for row in hf0_rows}
    assert {
        row["allowed_for_actor"]
        for row in hf0_rows
        if row["interface_component"] == "DIAGNOSTIC_ONLY_KEYS"
    } == {"False"}
    assert contract_snapshot["observation_shape"] == P0_OBSERVATION_DIM
    assert contract_snapshot["action_shape"] == ACTION_DIM
    assert contract_snapshot["all_baseline_checkpoints_admitted"] is True
    assert contract_snapshot["diagnostics_only_hidden_keys_count"] > 0

    for name in (
        "actor_io_contract_snapshot.md",
        "hf0_interface_contract.md",
        "materialization_gate_plan.md",
    ):
        assert (output_dir / name).read_text(encoding="utf-8").strip()
