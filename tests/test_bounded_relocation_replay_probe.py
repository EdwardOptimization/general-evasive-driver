import pandas as pd

from autodrift.bounded_relocation_replay_probe import (
    bounded_relocation_geometry,
    build_replay_summary,
    classify_actual_replay_result,
    select_replay_candidates,
)


def _candidate(
    *,
    seed: int,
    capability_pair: str,
    variant: str = "warmup_removed",
    sequence_l2: float = 0.10,
    margin_gap: float = 0.001,
    preferred_proxy: bool = True,
) -> dict[str, object]:
    return {
        "selected_index": seed,
        "source_index": seed + 100,
        "seed": seed,
        "reveal_step": 48,
        "preferred_fault": "preferred",
        "wrong_fault": "wrong",
        "variant": variant,
        "capability_pair": capability_pair,
        "preferred_reveal_bucket": f"bucket-{seed}",
        "sequence_action_l2_mean": sequence_l2,
        "margin_gap": margin_gap,
        "body_longitudinal_offset": -1.0,
        "body_lateral_offset": 0.2,
        "half_width_inflation": 0.1,
        "proxy_preferred_normal_margin": preferred_proxy,
    }


def test_select_replay_candidates_filters_controls_and_caps_pairs():
    frame = pd.DataFrame(
        [
            _candidate(seed=1, capability_pair="a->b", variant="zero_current_response", sequence_l2=0.8),
            _candidate(seed=2, capability_pair="a->b", variant="warmup_removed", sequence_l2=0.4),
            _candidate(seed=3, capability_pair="a->b", variant="warmup_shortened_8", sequence_l2=0.3),
            _candidate(seed=4, capability_pair="c->d", variant="delayed_warmup_history_8", sequence_l2=0.2),
        ]
    )

    selected = select_replay_candidates(
        frame,
        max_candidate_rows=10,
        per_capability_pair_cap=1,
        min_sequence_action_l2=0.025,
    )

    assert len(selected) == 2
    assert "zero_current_response" not in set(selected["variant"])
    assert selected["capability_pair"].value_counts().max() == 1


def test_bounded_relocation_geometry_clips_forward_distance_and_width():
    geometry = bounded_relocation_geometry(
        source_body_x=1.0,
        source_body_y=-0.5,
        source_half_width=0.2,
        body_longitudinal_offset=-5.0,
        body_lateral_offset=0.75,
        half_width_inflation=-1.0,
        min_body_x=2.0,
        min_half_width=0.05,
    )

    assert geometry["relocated_body_x"] == 2.0
    assert geometry["relocated_body_y"] == 0.25
    assert geometry["relocated_half_width"] == 0.05


def test_classify_actual_replay_counts_history_but_not_controls():
    history = classify_actual_replay_result(
        variant="warmup_removed",
        normal_success=True,
        variant_success=False,
        normal_margin=0.05,
        variant_margin=-0.01,
        sequence_action_l2_mean=0.04,
    )
    control = classify_actual_replay_result(
        variant="zero_current_response",
        normal_success=True,
        variant_success=False,
        normal_margin=0.05,
        variant_margin=-0.01,
        sequence_action_l2_mean=0.04,
    )
    noncritical = classify_actual_replay_result(
        variant="warmup_removed",
        normal_success=True,
        variant_success=True,
        normal_margin=0.05,
        variant_margin=0.049,
        sequence_action_l2_mean=0.04,
    )

    assert history["outcome_critical"] is True
    assert history["history_positive"] is True
    assert history["control_positive"] is False
    assert control["outcome_critical"] is True
    assert control["history_positive"] is False
    assert control["control_positive"] is True
    assert noncritical["history_positive"] is False


def test_build_replay_summary_emits_contract_flags(tmp_path):
    replay_rows = [
        {
            "seed": 1,
            "capability_pair": "a->b",
            "preferred_reveal_bucket": "bucket-a",
            "variant": "warmup_removed",
            "normal_success": True,
            "normal_margin": 0.05,
            "history_positive": True,
            "control_positive": False,
            "outcome_critical": True,
            "relocation_key": "x=4|y=0|w=1",
        },
        {
            "seed": 2,
            "capability_pair": "c->d",
            "preferred_reveal_bucket": "bucket-b",
            "variant": "zero_current_response",
            "normal_success": True,
            "normal_margin": 0.05,
            "history_positive": False,
            "control_positive": True,
            "outcome_critical": True,
            "relocation_key": "x=4|y=0|w=1",
        },
    ]

    summary = build_replay_summary(
        run_dir=tmp_path,
        candidate_rows=[{"seed": 1, "capability_pair": "a->b", "preferred_reveal_bucket": "bucket-a"}],
        replay_rows=replay_rows,
        rejected_rows=[],
        actor_parameters_changed=False,
        min_margin_gap=0.02,
        min_sequence_action_l2=0.025,
    )

    assert summary["selected_candidate_rows"] == 1
    assert summary["actual_replay_rows"] == 2
    assert summary["history_positive_rows"] == 1
    assert summary["control_positive_rows"] == 1
    assert summary["training_started"] is False
    assert summary["ppo_used"] is False
    assert summary["promoted"] is False
    assert summary["actor_input_contract_changed"] is False
