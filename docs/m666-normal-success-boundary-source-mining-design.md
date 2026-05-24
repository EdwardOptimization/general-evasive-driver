# M666 Normal-Success Boundary Source Mining Design

## Purpose

M666 designs the next no-training miner after M664/M665 showed that broader
wrong-history source mining can create action gaps, but the action-sensitive
rows occur in already-failed normal-history states.

The goal is to make the preferred branch valid before wrong-history pairing:

```text
normal history succeeds
normal margin is positive but near boundary
wrong history changes short-horizon action
wrong history loses margin or success
```

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## Key Change

M664 source order:

```text
1. pick close obstacle-visible snapshots
2. pair wrong histories
3. discover action gaps in already-failed normal states
```

M667 source order:

```text
1. build a wider obstacle decision-window snapshot bank
2. replay normal-history continuation first
3. classify source windows by normal outcome and margin
4. pair wrong histories only for normal-success near-boundary windows
5. keep early-safe and already-failed windows as diagnostics only
```

This is a source-window fix, not a threshold weakening.

## Snapshot Bank

M667 should use the same BC5660 checkpoint and fresh/OOD configs:

```text
checkpoint:
  runs/m568_scaled_l3_bc_seed5660/checkpoint.pt

surfaces:
  fresh=configs/ppo_m541_matched_l3_variance_4096.json
  ood=configs/eval_m574_moderate_ood_l3.json

seed ranges:
  fresh=25560:25619
  ood=25660:25719
```

Unlike M664, it should not only keep the closest obstacle-visible snapshots.
It should sample a wider decision window:

```text
obstacle_distance_min: 0.0 m
obstacle_distance_max: 35.0 m
sample_stride: 3
max_snapshots_per_seed: 8
max_snapshots_per_surface: 480
```

Each raw snapshot should store:

```text
observation
normal_hidden
env snapshot
surface
seed
step
obstacle x/y in ego frame
scene-context vector
ego-response vector
```

Metadata stays outside actor input.

## Normal-Outcome Prepass

Before pairing wrong histories, M667 should replay the normal branch from each
candidate left snapshot and compute:

```text
normal_success
normal_collision
normal_terminal_reason
normal_margin
normal_risk_score
normal_first_action
normal_action_sequence for K in {5, 7, 9}
```

Then classify source windows:

```text
near_boundary_preferred:
  normal_success == true
  0.000 <= normal_margin <= 1.000

early_safe_diagnostic:
  normal_success == true
  normal_margin > 1.000

already_failed_diagnostic:
  normal_success == false
  or normal_margin < 0.000
```

Only `near_boundary_preferred` may enter accepted wrong-history pairing.
`early_safe_diagnostic` and `already_failed_diagnostic` should still be reported
to explain negative results and avoid repeating M664.

If near-boundary rows are too few, M667 should report that as a source-window
coverage failure rather than weakening the wrong-history gate.

## Wrong-History Pairing

For each near-boundary left snapshot, sample compatible right-hidden sources
from the same surface first.

Compatibility filters:

```text
left_seed != right_seed
context_distance <= 0.25
response_distance <= 0.20
obstacle_x_abs_delta <= 10.0 m
obstacle_y_abs_delta <= 2.0 m
step_abs_delta <= 30
max_right_candidates_per_left <= 64
max_candidate_pairs_per_surface <= 1600
```

The obstacle caps are slightly wider than M664 because M667 samples a wider
decision window, but current scene compatibility remains mandatory.

Ranking:

```text
1. larger hidden distance
2. closer context distance
3. closer response distance
4. source diversity
```

Hidden distance is proposal ranking only, never acceptance.

## Acceptance Thresholds

Use the same action/outcome thresholds as M664:

```text
wrong_first_action_l2 >= 0.002
wrong_action_sequence_mean_l2 >= 0.006
preferred_vs_rejected_action_mean_l2 >= 0.010
normal_success == true
normal_margin >= 0.000
success_drop or margin_gap >= 0.010
wrong_margin <= normal_margin - 0.010 unless success_drop is true
```

Do not accept normal-failed preferred branches.

## Required Artifacts

M667 should write:

```text
runs/m667_normal_success_boundary_source_miner/summary.json
runs/m667_normal_success_boundary_source_miner/snapshot_bank_summary.csv
runs/m667_normal_success_boundary_source_miner/normal_window_summary.csv
runs/m667_normal_success_boundary_source_miner/candidate_scores.csv
runs/m667_normal_success_boundary_source_miner/normal_success_boundary_rows.csv
runs/m667_normal_success_boundary_source_miner/normal_success_boundary_corpus.npz
runs/m667_normal_success_boundary_source_miner/source_summary.csv
runs/m667_normal_success_boundary_source_miner/split_summary.csv
runs/m667_normal_success_boundary_source_miner/target_summary.csv
docs/m667-normal-success-boundary-source-miner-implementation.md
```

The NPZ should preserve the sequence corpus contract:

```text
observation
normal_hidden
variant_hidden
preferred_action_sequence
rejected_action_sequence
target_action_sequence
normal_base_action_sequence
variant_base_action_sequence
sequence_mask
variant_base_action
weight
row_id
source_index
sequence_length
```

## Pass Criteria

M667 passes source mining only if:

```text
near_boundary_preferred left snapshots >= 40
accepted rows >= 40
accepted physical pairs >= 8
accepted left seeds >= 6
accepted right seeds >= 6
source-heldout split nonempty
mean preferred_vs_rejected_action_mean_l2 >= 0.010
mean margin_gap >= 0.010 or accepted success_drop_rate >= 0.25
actor checksum unchanged
no actor checkpoint written
no optimizer/PPO used
```

This remains corpus infrastructure, not promotion.

## Negative Result Interpretation

M667 should distinguish three failures:

```text
no_near_boundary_normal_success_windows:
  The current seed/config family does not expose enough valid preferred
  decision windows. Next branch should tune scenario/window mining, not actor.

near_boundary_exists_but_no_action_gap:
  Valid preferred windows exist, but wrong histories do not change actions.
  Next branch should revisit representation/action-boundary design.

near_boundary_action_gap_but_no_outcome_gap:
  Wrong histories change actions but do not affect margin/success. Next branch
  should seek sharper boundary windows or longer-horizon outcome scoring.
```

Do not collapse these into a generic "failed" result.

## Forbidden Shortcuts

Do not:

- train;
- run PPO;
- promote a checkpoint;
- accept normal-failed preferred branches;
- use hidden-distance-only rows;
- weaken M664/M667 thresholds after seeing weak results;
- expose hidden parameters, labels, or feasibility metadata to actor input.

## Decision

```text
normal_success_boundary_source_mining_design_admit_m667
```

## Next

```text
m667-normal-success-boundary-source-miner-implementation
```
