import csv

import numpy as np
import torch

from autodrift.env import AutoDriftEnv, DriftEnvConfig, ObstacleTaskConfig
from autodrift.extreme_dynamics_scenario_corpus import FaultSpec
from autodrift.temporal_action_boundary_outcome_miner import (
    _accepted_boundary_row,
    classify_boundary_miner_result,
    load_source_rows,
    relocate_temporal_snapshot,
)
from autodrift.temporal_action_response_mismatch import TemporalSnapshot


def test_classify_boundary_positive_requires_outcome_and_diversity():
    result = classify_boundary_miner_result(
        candidate_variant_count=300,
        accepted_rows=35,
        temporal_action_critical_rows=80,
        temporal_outcome_critical_rows=22,
        unique_fault_families=4,
        unique_seeds=10,
        max_fault_family_dominance=0.35,
        normal_history_retention_pass=True,
        sentinel_false_positive_rate=0.0,
        normal_failed_rejected=4,
    )

    assert result == "temporal_outcome_boundary_positive"


def test_classify_boundary_artifact_on_sentinel_false_positive_rate():
    result = classify_boundary_miner_result(
        candidate_variant_count=300,
        accepted_rows=35,
        temporal_action_critical_rows=80,
        temporal_outcome_critical_rows=22,
        unique_fault_families=4,
        unique_seeds=10,
        max_fault_family_dominance=0.35,
        normal_history_retention_pass=True,
        sentinel_false_positive_rate=0.20,
        normal_failed_rejected=4,
    )

    assert result == "boundary_miner_artifact"


def test_accepted_boundary_row_requires_temporal_action_and_outcome():
    base = {
        "source_role": "primary",
        "variant": "mismatch_zero_command_history",
        "temporal_action_critical": True,
        "temporal_outcome_critical": True,
    }

    assert _accepted_boundary_row(base)
    assert not _accepted_boundary_row({**base, "source_role": "sentinel"})
    assert not _accepted_boundary_row({**base, "variant": "reset_hidden"})
    assert not _accepted_boundary_row({**base, "temporal_action_critical": False})


def test_load_source_rows_balances_primary_and_sentinel(tmp_path):
    path = tmp_path / "temporal.csv"
    fields = [
        "pair_id",
        "seed",
        "step",
        "preferred_fault",
        "preferred_fault_family",
        "preferred_fault_severity",
        "wrong_fault",
        "wrong_fault_family",
        "wrong_fault_severity",
        "source_pool",
        "variant",
        "normal_success",
        "normal_margin",
        "temporal_action_critical",
        "action_critical",
        "first_action_distance_from_normal",
    ]
    rows = []
    for index in range(12):
        rows.append(
            {
                "pair_id": str(index),
                "seed": str(72000 + index % 3),
                "step": "40",
                "preferred_fault": f"fault_{index}",
                "preferred_fault_family": f"family_{index % 4}",
                "preferred_fault_severity": "severe",
                "wrong_fault": "wrong",
                "wrong_fault_family": "wrong_family",
                "wrong_fault_severity": "extreme",
                "source_pool": "m713_low_alpha_family",
                "variant": "mismatch_zero_command_history",
                "normal_success": "True",
                "normal_margin": "1.0",
                "temporal_action_critical": "True",
                "action_critical": "True",
                "first_action_distance_from_normal": "0.02",
            }
        )
    for index in range(3):
        rows.append(
            {
                "pair_id": str(100 + index),
                "seed": str(72000 + index),
                "step": "44",
                "preferred_fault": f"sentinel_{index}",
                "preferred_fault_family": "sentinel_family",
                "preferred_fault_severity": "mild",
                "wrong_fault": "wrong",
                "wrong_fault_family": "wrong_family",
                "wrong_fault_severity": "severe",
                "source_pool": "m716_general",
                "variant": "mismatch_zero_command_history",
                "normal_success": "True",
                "normal_margin": "1.0",
                "temporal_action_critical": "False",
                "action_critical": "False",
                "first_action_distance_from_normal": "0.001",
            }
        )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    selected = load_source_rows(
        path,
        seed_start=72000,
        seed_count=4,
        max_source_rows=10,
        min_action_l2_gap=0.015,
        sentinel_fraction=0.2,
    )

    assert len(selected) == 10
    assert any(row["source_role"] == "sentinel" for row in selected)
    assert len({row["preferred_fault_family"] for row in selected if row["source_role"] == "primary"}) > 1


def test_relocate_temporal_snapshot_does_not_mutate_original_observation():
    config = DriftEnvConfig(
        max_steps=20,
        obstacle=ObstacleTaskConfig(enabled=True, distance_range=(30.0, 30.0), half_width_range=(1.0, 1.0)),
    )
    env = AutoDriftEnv(config)
    obs, info = env.reset(seed=1)

    snapshot = TemporalSnapshot(
        snapshot_id=1,
        scenario_id="seed1_fault",
        seed=1,
        fault=FaultSpec(name="fault", family="family", severity="severe", activation_step=0, params={}),
        step=40,
        observation=obs,
        hidden=torch.zeros(1, 16),
        env=env,
        info=info,
        obstacle_distance=30.0,
        obstacle_lateral_offset=0.0,
        history_steps=(),
        history_observations=(),
        history_start_hidden=torch.zeros(1, 16),
        delayed_hiddens={},
        pre_fault_hidden=None,
    )
    original = snapshot.observation.copy()

    relocated = relocate_temporal_snapshot(snapshot, body_longitudinal=20.0, body_lateral=0.5, half_width=1.2)

    assert np.array_equal(snapshot.observation, original)
    assert relocated.obstacle_distance == 20.0
    assert relocated.obstacle_lateral_offset == 0.5
