import pytest

from autodrift.decisive_history_candidate_planner import (
    CandidatePlannerConfig,
    CandidateSourcePlan,
    default_source_plans,
    generate_candidates,
    generate_candidates_from_plan,
    run_candidate_planner_smoke,
    validate_source_plan,
)


def test_default_source_plans_cover_t4_and_t5_public_families():
    plans = default_source_plans(seed_count=1)

    assert {plan.task_family for plan in plans} == {"T4", "T5"}
    assert {plan.source_family for plan in plans} == {
        "t4_staged_warmup_capability",
        "t4_capability_step_temporal",
        "t4_actuator_delay_response",
        "t5_near_boundary_warmup",
        "t5_high_speed_close_obstacle",
        "t5_boundary_axis_retarget",
    }
    assert all(plan.labels_enter_actor_input is False for plan in plans)


def test_validate_source_plan_rejects_shortcuts_and_missing_shape():
    plan = CandidateSourcePlan(
        source_family="bad",
        task_family="T4",
        seed_base=1,
        seed_count=0,
        capability_pairs=(),
        geometry_keys=("g",),
        reveal_steps=(10,),
        labels_enter_actor_input=True,
    )

    errors = validate_source_plan(plan)

    assert "nonpositive_seed_count" in errors
    assert "missing_capability_pairs" in errors
    assert "labels_enter_actor_input" in errors


def test_generate_candidates_from_plan_emits_m1500_compatible_rows():
    plan = CandidateSourcePlan(
        source_family="t4_test",
        task_family="T4",
        seed_base=10,
        seed_count=2,
        capability_pairs=("a|b",),
        geometry_keys=("left", "right"),
        reveal_steps=(20,),
        older_history_distance=0.2,
        normal_margin=0.08,
        action_divergence=0.05,
        intervention_margins={"wrong_history": 0.01},
    )

    candidates = generate_candidates_from_plan(plan)

    assert len(candidates) == 2
    assert candidates[0].candidate_id == "t4_test-000"
    assert candidates[0].decision_step == 28
    assert candidates[1].geometry_key == "right"
    assert candidates[0].labels_enter_actor_input is False


def test_generate_candidates_rejects_invalid_plan():
    config = CandidatePlannerConfig(
        source_plans=(
            CandidateSourcePlan(
                source_family="invalid",
                task_family="T6",
                seed_base=1,
                seed_count=1,
                capability_pairs=("a|b",),
                geometry_keys=("g",),
                reveal_steps=(1,),
            ),
        )
    )

    with pytest.raises(ValueError, match="unknown_task_family"):
        generate_candidates(config)


def test_candidate_planner_smoke_writes_no_training_artifacts(tmp_path):
    summary = run_candidate_planner_smoke(tmp_path / "planner", seed_count=2)
    harness = summary["harness"]

    assert summary["result_class"] == "decisive_history_candidate_planner_summary"
    assert summary["source_plan_count"] == 6
    assert summary["generated_candidate_rows"] == 12
    assert harness["accepted_t4_count"] == 6
    assert harness["accepted_t5_count"] == 6
    assert harness["source_diversity"]["unique_seeds"] == 12
    assert harness["source_diversity"]["max_source_share"] == pytest.approx(1.0 / 12.0)
    assert summary["training_started"] is False
    assert summary["replay_started"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert summary["private_holdout_used"] is False
    assert summary["actor_input_contract_changed"] is False
    assert summary["training_corpus_exported"] is False
    assert summary["labels_enter_actor_input"] is False
    assert (tmp_path / "planner" / "source_plan_rows.csv").exists()
    assert (tmp_path / "planner" / "candidate_rows.csv").exists()
    assert (tmp_path / "planner" / "source_family_summary.csv").exists()
    assert (tmp_path / "planner" / "summary.json").exists()
