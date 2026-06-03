import csv
import json

from autodrift.engineering_controller_behavior_outcome_protocol import (
    AUDIT_GATE_FIELDNAMES,
    LAYER_REGISTRY_FIELDNAMES,
    METRIC_REGISTRY_FIELDNAMES,
    ROW_SCHEMA_FIELDNAMES,
    materialize_behavior_outcome_protocol,
)


FALSE_CLAIM_FLAGS = [
    "environment_rollout_run",
    "simulator_step_run",
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


def _read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_materialize_behavior_outcome_protocol_writes_schema_and_registries(tmp_path):
    out = tmp_path / "run"

    summary = materialize_behavior_outcome_protocol(
        out,
        milestone="m2514-test",
        next_blocker="m2515-test",
    )

    assert summary["status_pass"] is True
    assert (
        summary["result_class"]
        == "engineering_controller_behavior_outcome_protocol_materialization_pass"
    )
    assert summary["protocol_version"] == "engineering_controller_behavior_outcome_v0"
    assert summary["required_artifacts_present"] is True
    assert summary["source_artifacts_exist"] is True
    assert summary["missing_source_artifacts"] == []
    assert summary["actor_contract_shape_72_action_3"] is True
    assert summary["actor_contract"]["observation_shape"] == 72
    assert summary["actor_contract"]["action_shape"] == 3
    assert summary["actor_contract"]["actor_encoder"] == "human_view_online_gru"
    assert summary["no_hidden_oracle_actor_inputs_encoded"] is True
    assert summary["forbidden_actor_inputs_encoded"] is True
    assert summary["forbidden_outcome_shortcuts_encoded"] is True
    assert summary["claim_boundary_encoded"] is True
    assert summary["ranking_or_winner_fields_emitted"] is False
    assert summary["success_rate_verdict_field_emitted"] is False
    assert summary["no_rollout_scope"] is True
    assert summary["source_only_layer_separated_from_validation"] is True
    assert summary["taxonomy_row_count"] >= 8

    for flag in FALSE_CLAIM_FLAGS:
        assert summary[flag] is False

    for filename in [
        "summary.json",
        "protocol_schema.json",
        "row_schema.csv",
        "metric_registry.csv",
        "audit_gate_registry.csv",
        "layer_registry.csv",
        "forbidden_registry.csv",
    ]:
        assert (out / filename).exists()

    summary_on_disk = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary_on_disk == summary


def test_behavior_outcome_registries_encode_contract_layers_and_forbidden_shortcuts(tmp_path):
    out = tmp_path / "run"
    materialize_behavior_outcome_protocol(out)

    row_schema = _read_csv(out / "row_schema.csv")
    metric_registry = _read_csv(out / "metric_registry.csv")
    audit_gates = _read_csv(out / "audit_gate_registry.csv")
    layers = _read_csv(out / "layer_registry.csv")
    forbidden = _read_csv(out / "forbidden_registry.csv")
    protocol = json.loads((out / "protocol_schema.json").read_text(encoding="utf-8"))

    assert set(row_schema[0]) == set(ROW_SCHEMA_FIELDNAMES)
    assert set(metric_registry[0]) == set(METRIC_REGISTRY_FIELDNAMES)
    assert set(audit_gates[0]) == set(AUDIT_GATE_FIELDNAMES)
    assert set(layers[0]) == set(LAYER_REGISTRY_FIELDNAMES)

    row_fields = {row["field_name"] for row in row_schema}
    assert {
        "evidence_layer",
        "scenario_role",
        "actor_contract_id",
        "observation_shape",
        "action_shape",
        "minimum_obstacle_clearance_m",
        "metric_completeness_flags",
        "diagnostic_only_no_ranking_claim",
        "forbidden_interpretation",
        "source_artifact",
    }.issubset(row_fields)

    metric_names = {row["metric_name"] for row in metric_registry}
    assert {
        "collision_event",
        "obstacle_passed_event",
        "road_departure_event",
        "recovery_time_proxy_s",
        "mitigation_delta_against_reference",
        "diagnostic_only_no_ranking_claim",
    }.issubset(metric_names)

    layer_names = {row["evidence_layer"] for row in layers}
    assert {
        "source_only_diagnostic",
        "current_sim_diagnostic_mining",
        "future_high_fidelity_validation",
    }.issubset(layer_names)
    assert {
        row["forbidden_interpretation"]
        for row in layers
        if row["evidence_layer"] == "source_only_diagnostic"
    } == {"driver performance or scenario generalization"}

    gate_ids = {row["gate_id"] for row in audit_gates}
    assert {
        "actor_contract_72_3",
        "no_hidden_oracle_actor_inputs",
        "layer_separation_preserved",
        "no_ranking_or_winner_fields",
        "source_only_diagnostic_claim_only",
    }.issubset(gate_ids)

    forbidden_items = {row["forbidden_signal_or_shortcut"] for row in forbidden}
    assert {
        "mu",
        "ttc",
        "required_clearance",
        "mixed_role_success_rate_aggregate",
        "controller_ranking",
        "winner_selection",
        "high_fidelity_validation_readiness_from_source_only_rows",
        "level3_self_identification_conclusion",
    }.issubset(forbidden_items)

    assert protocol["actor_contract"]["observation_shape"] == 72
    assert protocol["actor_contract"]["action_shape"] == 3
    assert "environment_rollout" in protocol["forbidden_initial_operations"]
    assert "success_rate_verdict" in protocol["forbidden_initial_operations"]
