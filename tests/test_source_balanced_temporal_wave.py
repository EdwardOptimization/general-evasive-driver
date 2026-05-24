import numpy as np
import torch

from autodrift.extreme_dynamics_scenario_corpus import FaultSpec, pairing_rule_from_dict
from autodrift.source_balanced_temporal_wave import (
    PairProposal,
    classify_source_balanced_temporal_wave,
    collect_pair_proposals,
    select_balanced_proposals,
)
from autodrift.temporal_action_response_mismatch import TemporalSnapshot


def _snapshot(seed, fault_name, family, severity, step=40, snapshot_id=0):
    return TemporalSnapshot(
        snapshot_id=snapshot_id,
        scenario_id=f"seed{seed}_{fault_name}",
        seed=seed,
        fault=FaultSpec(name=fault_name, family=family, severity=severity, activation_step=0, params={}),
        step=step,
        observation=np.zeros(72, dtype=np.float32),
        hidden=torch.zeros(1, 16),
        env=None,
        info={},
        obstacle_distance=40.0,
        obstacle_lateral_offset=0.0,
        history_steps=(),
        history_observations=(),
        history_start_hidden=torch.zeros(1, 16),
        delayed_hiddens={},
        pre_fault_hidden=None,
    )


def test_classify_source_balanced_outcome_positive():
    result = classify_source_balanced_temporal_wave(
        proposal_count=5000,
        selected_pair_count=4096,
        temporal_action_critical_rows=500,
        temporal_outcome_critical_rows=25,
        unique_selected_seeds=256,
        unique_preferred_fault_families=8,
        unique_fault_family_pairs=24,
        max_seed_dominance=0.01,
        max_preferred_family_dominance=0.20,
        sentinel_false_positive_rate=0.0,
        normal_history_retention_pass=True,
        actor_parameters_changed=False,
    )

    assert result == "source_balanced_temporal_outcome_positive"


def test_classify_source_balance_blocked_when_seed_dominates():
    result = classify_source_balanced_temporal_wave(
        proposal_count=5000,
        selected_pair_count=4096,
        temporal_action_critical_rows=500,
        temporal_outcome_critical_rows=0,
        unique_selected_seeds=4,
        unique_preferred_fault_families=8,
        unique_fault_family_pairs=24,
        max_seed_dominance=0.40,
        max_preferred_family_dominance=0.20,
        sentinel_false_positive_rate=0.0,
        normal_history_retention_pass=True,
        actor_parameters_changed=False,
    )

    assert result == "source_balance_blocked"


def test_select_balanced_proposals_respects_per_seed_cap():
    proposals = []
    proposal_id = 0
    for seed in range(10):
        for index in range(5):
            snap = _snapshot(seed, f"front_{seed}_{index}", "front", "severe", snapshot_id=proposal_id)
            wrong = _snapshot(seed, f"rear_{seed}_{index}", "rear", "severe", snapshot_id=proposal_id + 100)
            proposals.append(
                PairProposal(
                    proposal_id=proposal_id,
                    snapshot=snap,
                    wrong_snapshot=wrong,
                    match_distance=float(index),
                    pairing_rule="front->rear",
                    source_pool="test",
                )
            )
            proposal_id += 1

    selected = select_balanced_proposals(
        proposals,
        selected_pair_count=100,
        per_seed_pair_cap=2,
        per_fault_family_pair_cap=100,
        per_preferred_family_cap=100,
        per_step_bucket_cap=100,
    )

    counts = {}
    for proposal in selected:
        counts[proposal.snapshot.seed] = counts.get(proposal.snapshot.seed, 0) + 1
    assert len(selected) == 20
    assert max(counts.values()) == 2
    assert len(counts) == 10


def test_collect_pair_proposals_uses_low_alpha_source_pool():
    snapshots = [
        _snapshot(1, "front", "front_lateral_authority_drop", "severe", snapshot_id=1),
        _snapshot(1, "rear", "rear_lateral_authority_drop", "severe", snapshot_id=2),
    ]
    rules = (
        pairing_rule_from_dict({
            "preferred_family": "front_lateral_authority_drop",
            "wrong_family": "rear_lateral_authority_drop",
        }),
    )

    proposals = collect_pair_proposals(
        snapshots=snapshots,
        pairing_rules=rules,
        low_alpha_pairs={"front_lateral_authority_drop->rear_lateral_authority_drop"},
    )

    assert proposals
    assert proposals[0].source_pool == "m713_low_alpha_family"
