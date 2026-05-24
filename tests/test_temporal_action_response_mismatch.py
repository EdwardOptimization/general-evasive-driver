import numpy as np
import torch

from autodrift.extreme_dynamics_scenario_corpus import FaultSpec
from autodrift.temporal_action_response_mismatch import (
    TemporalSnapshot,
    _row_for_variant,
    build_temporal_variant_hiddens,
    classify_temporal_mismatch_result,
)
from autodrift.train_ppo import ActorCritic


def _snapshot(hidden, *, fault=None):
    obs0 = np.zeros(72, dtype=np.float32)
    obs1 = np.zeros(72, dtype=np.float32)
    obs1[9:12] = np.asarray([0.2, -0.1, 0.5], dtype=np.float32)
    fault = fault or FaultSpec(
        name="front_proxy",
        family="front_lateral_authority_drop",
        severity="severe",
        activation_step=10,
        params={},
    )
    return TemporalSnapshot(
        snapshot_id=1,
        scenario_id="seed1_front_proxy",
        seed=1,
        fault=fault,
        step=32,
        observation=np.zeros(72, dtype=np.float32),
        hidden=hidden,
        env=None,
        info={},
        obstacle_distance=40.0,
        obstacle_lateral_offset=0.0,
        history_steps=(30, 31),
        history_observations=(obs0, obs1),
        history_start_hidden=torch.zeros_like(hidden),
        delayed_hiddens={5: torch.ones_like(hidden) * 0.1},
        pre_fault_hidden=torch.ones_like(hidden) * 0.2,
    )


def test_classify_temporal_mismatch_positive_requires_diversity_and_retention():
    result = classify_temporal_mismatch_result(
        row_count=100,
        temporal_action_critical_rows=40,
        temporal_outcome_critical_rows=12,
        reset_action_critical_rows=20,
        reset_outcome_critical_rows=10,
        normal_history_retention_pass=True,
        unique_temporal_fault_families=4,
        unique_temporal_seeds=20,
        min_temporal_action_rows=30,
        min_temporal_outcome_rows=10,
        min_unique_fault_families=4,
        min_unique_seeds=20,
    )

    assert result == "temporal_mismatch_positive"


def test_classify_temporal_mismatch_reset_only_when_temporal_rows_sparse():
    result = classify_temporal_mismatch_result(
        row_count=100,
        temporal_action_critical_rows=2,
        temporal_outcome_critical_rows=0,
        reset_action_critical_rows=20,
        reset_outcome_critical_rows=5,
        normal_history_retention_pass=True,
        unique_temporal_fault_families=1,
        unique_temporal_seeds=2,
        min_temporal_action_rows=30,
        min_temporal_outcome_rows=10,
        min_unique_fault_families=4,
        min_unique_seeds=20,
    )

    assert result == "temporal_reset_only"


def test_classify_temporal_mismatch_action_only_when_action_passes_without_outcomes():
    result = classify_temporal_mismatch_result(
        row_count=100,
        temporal_action_critical_rows=40,
        temporal_outcome_critical_rows=0,
        reset_action_critical_rows=20,
        reset_outcome_critical_rows=5,
        normal_history_retention_pass=True,
        unique_temporal_fault_families=4,
        unique_temporal_seeds=20,
        min_temporal_action_rows=30,
        min_temporal_outcome_rows=10,
        min_unique_fault_families=4,
        min_unique_seeds=20,
    )

    assert result == "temporal_action_only"


def test_classify_temporal_mismatch_artifact_on_empty_rows():
    result = classify_temporal_mismatch_result(
        row_count=0,
        temporal_action_critical_rows=0,
        temporal_outcome_critical_rows=0,
        reset_action_critical_rows=0,
        reset_outcome_critical_rows=0,
        normal_history_retention_pass=False,
        unique_temporal_fault_families=0,
        unique_temporal_seeds=0,
    )

    assert result == "temporal_artifact"


def test_build_temporal_variant_hiddens_adds_mismatch_variants_without_input_change():
    model = ActorCritic(obs_dim=72, act_dim=3, hidden_size=16, actor_encoder="human_view_online_gru")
    normal = _snapshot(torch.zeros(1, 16))
    wrong = _snapshot(torch.ones(1, 16) * 0.3)
    original_observation = normal.observation.copy()

    variants = build_temporal_variant_hiddens(
        model=model,
        snapshot=normal,
        wrong_snapshot=wrong,
        response_dim=12,
        device=torch.device("cpu"),
    )

    assert "normal" in variants
    assert "reset_hidden" in variants
    assert "cross_fault_wrong_hidden" in variants
    assert "delayed_hidden_5" in variants
    assert "pre_fault_stale_hidden" in variants
    assert "mismatch_zero_command_history" in variants
    assert "mismatch_command_shift_1" in variants
    assert "mismatch_response_delay_5" in variants
    assert np.array_equal(normal.observation, original_observation)


def test_row_for_variant_keeps_reset_separate_from_temporal_mismatch():
    pair_meta = {
        "pair_id": 1,
        "seed": 10,
        "preferred_fault_family": "front_lateral_authority_drop",
        "fault_family_pair": "front_lateral_authority_drop->steering_fault",
    }
    normal = {"success": True, "min_clearance_margin": 1.0}
    reset_result = {
        "success": True,
        "min_clearance_margin": 0.5,
        "first_action_distance": 0.02,
        "first_steer": 0.0,
        "first_throttle": 0.0,
        "first_brake": 0.0,
    }

    row = _row_for_variant(
        pair_meta=pair_meta,
        source_pool="m716_reset_only",
        variant="reset_hidden",
        result=reset_result,
        normal=normal,
        action_threshold=0.015,
        margin_threshold=0.02,
    )

    assert row["reset_action_critical"]
    assert row["reset_outcome_critical"]
    assert not row["temporal_action_critical"]
    assert not row["temporal_outcome_critical"]
