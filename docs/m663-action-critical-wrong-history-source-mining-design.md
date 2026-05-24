# M663 Action-Critical Wrong-History Source Mining Design

## Purpose

M663 designs the next source-mining branch after M661/M662 showed that the
existing M586/M636 matched-current surfaces are not action-divergent under
BC5660 wrong-history replay.

The goal is to mine rows where wrong history is not merely different in hidden
space, but action-critical:

```text
same compatible current scene/state
different command-response history
normal-history branch chooses one short-horizon maneuver
wrong-history branch chooses a distinct maneuver
wrong-history branch loses margin or success
```

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## Why M586/M636 Was Not Enough

M661 evaluated `3207` candidate rows from M586/M636 and accepted `0`.

The strongest candidate values were:

```text
max wrong_first_action_l2:                 0.004301
max wrong_action_sequence_mean_l2:         0.001850
max preferred_vs_rejected_action_mean_l2:  0.001850
max margin_gap:                            0.000031
```

This means the previous surfaces were useful for hidden/feature diagnostics but
not for training a wrong-history preference or rejected-action objective. They
do not produce meaningful short-horizon action divergence or outcome
sensitivity.

## Design Change

The next miner should invert the selection order.

Previous route:

```text
1. find matched-current / target-separated rows
2. replay wrong history
3. discover that actions and outcomes are almost unchanged
```

M664 route:

```text
1. build a broader snapshot bank
2. pair compatible current scenes with many candidate wrong histories
3. score action-sequence divergence and margin/success sensitivity
4. only then accept source rows
```

Hidden distance may be used to propose candidate wrong histories, but it must
not be an acceptance criterion by itself.

## Snapshot Bank

M664 should build or reuse a snapshot bank from the BC5660 checkpoint:

```text
checkpoint:
  runs/m568_scaled_l3_bc_seed5660/checkpoint.pt

surfaces:
  fresh=configs/ppo_m541_matched_l3_variance_4096.json
  ood=configs/eval_m574_moderate_ood_l3.json

seed ranges:
  fresh: 25560-25619
  ood:   25660-25719
```

For each episode, collect snapshots at obstacle-visible and decision-relevant
steps. Store:

```text
observation
normal_hidden
env snapshot
seed
step
surface
target proxy for logging only
obstacle geometry summary for logging only
road/free-space context vector
current ego-response vector
normal first action
normal K-step action sequence
normal rollout outcome
```

The actor input contract remains unchanged. Hidden parameters, labels, and
oracle feasibility are logging/mining metadata only and never enter actor
observations.

## Candidate Pairing

For each left/current snapshot, sample right/wrong-history candidates from the
snapshot bank.

Hard compatibility filters:

```text
left_seed != right_seed
same surface preferred; cross-surface allowed only in diagnostic tier
obstacle/free-space context distance <= context_threshold
current ego-response distance <= response_threshold
absolute obstacle x/y differences within fixed caps if available
right snapshot must have a valid recurrent hidden state
```

Initial thresholds:

```text
context_distance <= 0.25
response_distance <= 0.20
obstacle_x_abs_delta <= 8.0 m
obstacle_y_abs_delta <= 1.5 m
step_abs_delta <= 20
max right candidates per left snapshot: 64
max scored candidate pairs per surface: 1200
```

Ranking within compatible candidates:

```text
1. larger stored hidden distance
2. larger historical response-envelope difference if available
3. closer context distance
4. different physical seed pair
```

These ranking signals only propose wrong histories. Acceptance still requires
action and outcome evidence.

## Scoring

For every candidate pair:

1. Replay normal history from the left snapshot.
2. Replay wrong matched history from the left observation with the right hidden.
3. Build `K in {5, 7, 9}` action prefixes for both branches.
4. Compute action distances:

```text
wrong_first_action_l2
wrong_action_sequence_mean_l2
wrong_action_sequence_max_l2
preferred_vs_rejected_action_mean_l2
```

5. Compute outcome gaps:

```text
normal_success
wrong_success
success_drop = normal_success and not wrong_success
normal_margin
wrong_margin
margin_gap = normal_margin - wrong_margin
normal_risk_score
wrong_risk_score
risk_gap = wrong_risk_score - normal_risk_score
```

6. Keep row-level diagnostics even for rejected candidates.

## Acceptance Tiers

Strict action-critical acceptance:

```text
wrong_first_action_l2 >= 0.002
wrong_action_sequence_mean_l2 >= 0.006
preferred_vs_rejected_action_mean_l2 >= 0.010
normal_margin >= 0.000
success_drop or margin_gap >= 0.010
wrong_margin <= normal_margin - 0.010 unless success_drop is true
```

Near-miss diagnostics should be recorded but not used for training admission:

```text
action_only_near_miss:
  action thresholds pass but margin gap fails

outcome_only_near_miss:
  margin/success gap passes but action thresholds fail

compatibility_near_miss:
  action/outcome criteria pass only outside scene compatibility limits
```

If strict rows are too few, M664 should not weaken thresholds inside the same
milestone. It should report which near-miss category dominates.

## Diversity Rules

M664 should require:

```text
accepted rows >= 40
accepted physical pairs >= 8
accepted left seeds >= 6
accepted right seeds >= 6
targets/proxy targets >= 2
surfaces >= 1 required, 2 preferred
source-heldout split nonempty
max rows per physical pair fraction <= 0.20
max rows per left seed fraction <= 0.25
max rows per source_index fraction <= 0.25
```

Splits must be source-aware:

```text
train
source_holdout_validation
```

The heldout split should hold out whole physical seed pairs where possible.

## Required Artifacts

M664 should write:

```text
runs/m664_action_critical_wrong_history_source_miner/summary.json
runs/m664_action_critical_wrong_history_source_miner/snapshot_bank_summary.csv
runs/m664_action_critical_wrong_history_source_miner/candidate_scores.csv
runs/m664_action_critical_wrong_history_source_miner/action_critical_rows.csv
runs/m664_action_critical_wrong_history_source_miner/action_critical_corpus.npz
runs/m664_action_critical_wrong_history_source_miner/source_summary.csv
runs/m664_action_critical_wrong_history_source_miner/split_summary.csv
runs/m664_action_critical_wrong_history_source_miner/target_summary.csv
docs/m664-action-critical-wrong-history-source-miner-implementation.md
```

The NPZ should preserve the M661 field contract:

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

M664 passes as source mining only if:

```text
accepted rows >= 40
accepted physical pairs >= 8
accepted left seeds >= 6
accepted right seeds >= 6
source-heldout split nonempty
mean preferred_vs_rejected_action_mean_l2 >= 0.010
mean margin_gap >= 0.010 or success_drop_rate among accepted >= 0.25
actor checksum unchanged
no actor checkpoint written
no optimizer/PPO used
```

M664 is not a checkpoint promotion gate.

## Negative Result Interpretation

If M664 still finds no strict action-critical wrong-history rows, classify the
blocker as:

```text
no_action_critical_wrong_history_sources_found
```

That would mean BC5660's policy/action boundary is too insensitive to wrong
history under compatible current observations. The next branch should then
shift from corpus mining to representation/action-boundary design, for example:

```text
response-latent adapter with explicit action sensitivity
history-conditioned policy head shadow probe
training tasks that make hidden dynamics action-critical
```

Do not interpret such a negative result as proof that self-identification is
unnecessary. It would only say the current BC5660 checkpoint and current
scenario surfaces do not expose enough action-critical wrong-history evidence.

## Forbidden Shortcuts

Do not:

- use `mu`, labels, or feasibility flags as actor input;
- accept hidden-distance-only rows;
- relax thresholds after seeing weak action distances;
- train an actor/head in the miner milestone;
- use private holdouts;
- promote a checkpoint.

## Decision

```text
action_critical_wrong_history_source_mining_design_admit_m664
```

## Next

```text
m664-action-critical-wrong-history-source-miner-implementation
```
