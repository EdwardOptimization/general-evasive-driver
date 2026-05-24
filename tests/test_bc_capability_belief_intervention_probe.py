import numpy as np
import pandas as pd
import torch

from autodrift.bc_capability_belief_intervention_probe import (
    ALL_CAPABILITY_VARIANTS,
    build_capability_intervention_rows,
    capability_delta_metrics,
    capability_prediction_from_hidden,
    evaluate_actor_finetune_admission,
    summarize_capability_intervention_rows,
)
from autodrift.bc_capability_repair import CapabilityHead
from autodrift.matched_history_intervention_gate import RecurrentSnapshot
from autodrift.train_ppo import ActorCritic, HUMAN_VIEW_RESPONSE_FEATURE_DIM


def test_capability_prediction_from_hidden_uses_next_recurrent_hidden():
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=5,
        actor_encoder="human_view_online_gru",
    )
    head = CapabilityHead(hidden_size=5, output_dim=3)
    obs = np.ones(72, dtype=np.float32) * 0.1
    hidden = torch.zeros((1, 5), dtype=torch.float32)
    device = next(model.parameters()).device

    prediction, next_hidden = capability_prediction_from_hidden(
        model=model,
        head=head,
        observation=obs,
        hidden=hidden,
        device=device,
    )

    assert prediction.shape == (3,)
    assert next_hidden.shape == (1, 5)


def test_capability_delta_metrics_reports_z_distance_and_targets():
    row = capability_delta_metrics(
        normal_prediction=np.array([1.0, 2.0, 3.0], dtype=np.float32),
        variant_prediction=np.array([1.5, 1.0, 4.0], dtype=np.float32),
        target_std=np.array([0.5, 2.0, 1.0], dtype=np.float32),
        min_capability_z_distance=0.25,
    )

    assert row["capability_z_distance"] > 1.0
    assert row["capability_z_distance_above_threshold"] is True
    assert row["abs_z_future_braking_deceleration"] == 1.0
    assert row["abs_z_future_yaw_response"] == 0.5
    assert row["abs_z_future_lateral_accel_response"] == 1.0


def test_build_capability_intervention_rows_emits_required_variants_and_summaries():
    model = ActorCritic(
        obs_dim=72,
        act_dim=3,
        hidden_size=8,
        actor_encoder="human_view_online_gru",
    )
    head = CapabilityHead(hidden_size=8, output_dim=3)
    device = next(model.parameters()).device
    left_obs = np.zeros(72, dtype=np.float32)
    right_obs = np.ones(72, dtype=np.float32) * 0.1
    left_hidden = torch.zeros((1, 8), dtype=torch.float32)
    right_hidden = torch.ones((1, 8), dtype=torch.float32) * 0.5
    delayed_hidden = torch.ones((1, 8), dtype=torch.float32) * 0.2
    snapshots = {
        (10, 0): RecurrentSnapshot(seed=10, step=0, observation=left_obs, hidden=torch.ones((1, 8)) * 0.1),
        (10, 4): RecurrentSnapshot(seed=10, step=4, observation=left_obs, hidden=left_hidden),
        (20, 3): RecurrentSnapshot(seed=20, step=3, observation=right_obs, hidden=right_hidden),
        (30, 2): RecurrentSnapshot(seed=30, step=2, observation=right_obs + 0.1, hidden=delayed_hidden),
    }
    pair_rows = pd.DataFrame(
        [
            {
                "checkpoint_label": "bc",
                "source_checkpoint_label": "bc",
                "probe_seed": 6010,
                "target": "future_yaw_response",
                "left_seed": 10,
                "right_seed": 20,
                "left_step": 4,
                "right_step": 3,
                "target_z_delta": 1.5,
                "visible_distance": 0.1,
            }
        ]
    )

    rows = build_capability_intervention_rows(
        pair_rows=pair_rows,
        snapshots=snapshots,
        model=model,
        head=head,
        checkpoint_label="bc",
        surface="fresh",
        response_dim=HUMAN_VIEW_RESPONSE_FEATURE_DIM,
        delay_steps=4,
        target_std=np.ones(3, dtype=np.float32),
        min_capability_z_distance=0.0,
        device=device,
    )
    by_target, aggregate = summarize_capability_intervention_rows(rows)

    assert {row["variant"] for row in rows} == set(ALL_CAPABILITY_VARIANTS)
    assert all(row["checkpoint_label"] == "bc" for row in rows)
    assert all(row["surface"] == "fresh" for row in rows)
    assert len(by_target) == len(ALL_CAPABILITY_VARIANTS)
    assert len(aggregate) == len(ALL_CAPABILITY_VARIANTS)
    assert next(row for row in rows if row["variant"] == "normal")["capability_z_distance"] == 0.0


def test_evaluate_actor_finetune_admission_requires_real_history_thresholds():
    rows = [
        {
            "checkpoint_label": "bc",
            "surface": "fresh",
            "variant": "wrong_matched_history",
            "capability_z_distance_mean": 0.12,
            "above_threshold_count": 16,
            "pair_count": 30,
        },
        {
            "checkpoint_label": "bc",
            "surface": "fresh",
            "variant": "random_hidden_unit",
            "capability_z_distance_mean": 9.0,
            "above_threshold_count": 30,
            "pair_count": 30,
        },
    ]

    admitted = evaluate_actor_finetune_admission(rows)
    blocked = evaluate_actor_finetune_admission(rows, min_mean=0.2)

    assert admitted["actor_finetune_design_admitted"] is True
    assert admitted["eligible_rows"][0]["variant"] == "wrong_matched_history"
    assert blocked["actor_finetune_design_admitted"] is False
