from autodrift.public_base_residual_direction_feasibility import (
    classify_residual_direction_feasibility,
)


def test_classify_residual_direction_feasibility_candidate():
    assert (
        classify_residual_direction_feasibility(
            actor_backbone_changed=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_keys=0,
            feasible_candidate_count=1,
            any_tail_lift=True,
            any_normal_retained_tail_lift=True,
            training_started=False,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_residual_direction_feasibility_candidate"
    )


def test_classify_residual_direction_feasibility_trust_region_conflict():
    assert (
        classify_residual_direction_feasibility(
            actor_backbone_changed=False,
            reconstruction_success_rate=1.0,
            metadata_missing_rows=0,
            missing_target_keys=0,
            feasible_candidate_count=0,
            any_tail_lift=True,
            any_normal_retained_tail_lift=False,
            training_started=False,
            ppo_used=False,
            promoted=False,
        )
        == "public_base_residual_direction_feasibility_trust_region_conflict"
    )
