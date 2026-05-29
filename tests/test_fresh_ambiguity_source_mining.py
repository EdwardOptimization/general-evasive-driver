import pytest

from autodrift.fresh_ambiguity_source_mining import (
    FreshAmbiguitySourceSpec,
    classify_source_row,
    default_source_specs,
    expand_source_spec,
    expand_source_specs,
    run_source_planner_smoke,
    validate_source_spec,
)


def test_default_source_specs_cover_existing_and_fresh_proxy_families():
    specs = default_source_specs(seed=1528, seed_count=1)
    families = {spec.source_family for spec in specs}

    assert {
        "t4_staged_warmup_capability",
        "t4_capability_step_temporal",
        "t4_actuator_delay_response",
        "t5_near_boundary_warmup",
        "t5_high_speed_close_obstacle",
        "t5_boundary_axis_retarget",
    }.issubset(families)
    assert {
        "capability_step_down",
        "brake_fade_or_loss_proxy",
        "drive_loss_proxy",
        "grip_loss_proxy",
        "late_reveal_boundary",
        "curved_boundary_obstacle",
    }.issubset(families)
    assert sum(1 for spec in specs if spec.proxy_fault_family) >= 3
    assert all(spec.labels_enter_actor_input is False for spec in specs)
    assert all(spec.actor_input_contract_changed is False for spec in specs)


def test_validate_source_spec_rejects_shortcuts_and_asymmetric_claims():
    bad = FreshAmbiguitySourceSpec(
        source_family="one_wheel_blowout",
        task_family="T5",
        seed_base=1,
        seed_count=1,
        hidden_capability_pairs=("left_tire_blowout|normal",),
        geometry_keys=("g",),
        reveal_steps=(10,),
        proxy_fault_family=True,
        simulator_scope="existing_public_source",
        labels_enter_actor_input=True,
        actor_input_contract_changed=True,
    )

    errors = validate_source_spec(bad)

    assert "proxy_fault_missing_symmetric_scope" in errors
    assert "labels_enter_actor_input" in errors
    assert "actor_input_contract_changed" in errors
    assert "asymmetric_fault_claim_in_source_family" in errors
    assert "asymmetric_fault_claim_in_source_values" in errors


def test_expand_source_spec_emits_matched_context_divergence_fields():
    spec = FreshAmbiguitySourceSpec(
        source_family="capability_step_down",
        task_family="T4",
        seed_base=100,
        seed_count=2,
        hidden_capability_pairs=("mu_nominal|mu_drop",),
        geometry_keys=("left", "right"),
        reveal_steps=(20,),
        simulator_scope="single_track_symmetric_proxy",
        proxy_fault_family=True,
        first_action_l2=0.07,
        prefix_action_l2=0.15,
        terminal_margin_gap=0.04,
    )

    rows = expand_source_spec(spec)
    classification = classify_source_row(rows[0])

    assert len(rows) == 2
    assert rows[0].seed == 100
    assert rows[0].decision_step == 28
    assert rows[1].geometry_key == "right"
    assert rows[0].proxy_fault_family is True
    assert rows[0].simulator_scope == "single_track_symmetric_proxy"
    assert classification.accepted is True


def test_classify_source_row_rejects_non_ambiguous_rows():
    spec = FreshAmbiguitySourceSpec(
        source_family="weak",
        task_family="T4",
        seed_base=1,
        seed_count=1,
        hidden_capability_pairs=("a|b",),
        geometry_keys=("g",),
        reveal_steps=(10,),
        older_evidence_distance=0.01,
        hidden_capability_distance=0.01,
        first_action_l2=0.0,
        prefix_action_l2=0.0,
        terminal_margin_gap=0.0,
    )
    row = expand_source_spec(spec)[0]

    classification = classify_source_row(row)

    assert classification.accepted is False
    assert "older_evidence_distance_too_small" in classification.reasons
    assert "hidden_capability_distance_too_small" in classification.reasons
    assert "first_action_l2_too_small" in classification.reasons
    assert "terminal_margin_gap_too_small" in classification.reasons


def test_expand_source_specs_rejects_invalid_spec():
    spec = FreshAmbiguitySourceSpec(
        source_family="invalid",
        task_family="T6",
        seed_base=1,
        seed_count=1,
        hidden_capability_pairs=("a|b",),
        geometry_keys=("g",),
        reveal_steps=(10,),
    )

    with pytest.raises(ValueError, match="unknown_task_family"):
        expand_source_specs((spec,))


def test_source_planner_smoke_writes_guarded_artifacts(tmp_path):
    summary = run_source_planner_smoke(tmp_path / "planner", seed=1528, seed_count=8)

    assert summary["result_class"] == "fresh_ambiguity_source_planner_summary"
    assert summary["source_plan_count"] == 14
    assert summary["generated_source_specs"] == 112
    assert summary["accepted_pair_candidates"] == 112
    assert summary["unique_source_families"] == 14
    assert summary["proxy_fault_family_count"] >= 3
    assert summary["max_single_source_family_share"] == pytest.approx(1.0 / 14.0)
    assert summary["max_closed_t5_subset_share"] == 0.0
    assert summary["passes_public_dry_gates"] is True
    assert summary["guardrail_violation_count"] == 0
    assert summary["candidate_materialized"] is False
    assert summary["training_started"] is False
    assert summary["replay_started"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert summary["private_holdout_used"] is False
    assert summary["actor_input_contract_changed"] is False
    assert summary["training_corpus_exported"] is False
    assert summary["labels_enter_actor_input"] is False
    assert (tmp_path / "planner" / "fresh_ambiguity_source_specs.csv").exists()
    assert (tmp_path / "planner" / "fresh_ambiguity_pair_candidates.csv").exists()
    assert (tmp_path / "planner" / "fresh_ambiguity_action_divergence.csv").exists()
    assert (tmp_path / "planner" / "fresh_ambiguity_trace_snapshots.csv").exists()
    assert (tmp_path / "planner" / "fresh_ambiguity_guardrail_summary.csv").exists()
    assert (tmp_path / "planner" / "summary.json").exists()
