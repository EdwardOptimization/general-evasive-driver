# M1061 V4 Public Base Post Short-Promotion Family-Intersection Corpus

## Purpose

M1061 implements and runs the family-intersection selector designed in M1060.
The goal is to filter the post-short-promotion refreshed boundary surface so a
compact row can be used as proof evidence only when it remains a success-drop
row under every short-PPO family checkpoint.

This milestone does not train the actor, run PPO, use private holdout, change
actor inputs, or promote a checkpoint.

## Implementation

Added:

```text
src/autodrift/family_intersection_boundary_selector.py
tests/test_family_intersection_boundary_selector.py
```

The selector:

1. converts accepted boundary rows into replay-gate-compatible metadata;
2. replays every source row under `short61049`, `short61050`, and
   `short61051`;
3. adds family proof fields such as `family_success_drop_count`,
   `family_all_normal_success`, `family_all_wrong_history_fail`,
   `family_min_margin_gap`, and `family_policy_failures`;
4. keeps only rows with normal-history success and wrong-history failure under
   all family policies;
5. prefers the stricter `family_max_wrong_history_margin <= -0.0001` subset
   when it remains source-diverse enough;
6. avoids duplicate boundary geometries before applying the per-physical-pair
   cap, so downstream objective conversion does not silently shrink the corpus.

## Selector Run

Input:

```text
runs/m1056_margin_bucket_width_0005/accepted_wrong_history_rows.csv
```

Family:

```text
short61049: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
short61050: runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt
short61051: runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

Command class:

```text
python -m autodrift.family_intersection_boundary_selector ...
```

Artifacts:

```text
runs/m1061_family_intersection_selector/summary.json
runs/m1061_family_intersection_selector/family_intersection_selected_rows.csv
runs/m1061_family_intersection_summary/summary.json
```

Result:

```text
source_rows: 315
family_replay_rows: 945
family_intersection_candidates: 305
candidate_physical_pairs: 15
candidate_targets: 3
selected_rows: 79
selected_physical_pairs: 15
selected_targets: 3
selection_pass: true
```

Per-source compact rows:

```text
short61049:
  selected_rows: 25
  physical_pairs: 14
  targets: 3
  selection_mode: strict_family_margin

short61050:
  selected_rows: 27
  physical_pairs: 15
  targets: 3
  selection_mode: strict_family_margin

short61051:
  selected_rows: 27
  physical_pairs: 15
  targets: 3
  selection_mode: strict_family_margin
```

The M1058 failed near-zero wrong-history rows are filtered out because they do
not satisfy all-family success-drop.

## Objective Sanity

Objective conversion used the M1058 settings:

```text
optimization_seeds: 10570,10571,10572
steps: 180
batch_size: 64
learning_rate: 0.0003
weight_decay: 0.001
hidden_dim: 96
```

Result:

```text
short61049:
  rows: 25
  physical_groups: 14
  targets: 3
  objective_pass: true
  seed_pass_count: 3 / 3

short61050:
  rows: 27
  physical_groups: 15
  targets: 3
  objective_pass: true
  seed_pass_count: 3 / 3

short61051:
  rows: 27
  physical_groups: 15
  targets: 3
  objective_pass: true
  seed_pass_count: 3 / 3
```

Objective artifacts:

```text
runs/m1061_short61049_boundary_outcome_corpus_seed10570/objective_summary.json
runs/m1061_short61050_boundary_outcome_corpus_seed10570/objective_summary.json
runs/m1061_short61051_boundary_outcome_corpus_seed10570/objective_summary.json
```

## Cross-Family Replay Sanity

All six source-to-candidate replay sanity gates passed:

```text
short61049 -> short61050: 25 / 25 success drops retained
short61049 -> short61051: 25 / 25 success drops retained
short61050 -> short61049: 27 / 27 success drops retained
short61050 -> short61051: 27 / 27 success drops retained
short61051 -> short61049: 27 / 27 success drops retained
short61051 -> short61050: 27 / 27 success drops retained
```

Every replay gate kept:

```text
normal_success_retention_pass: true
normal_margin_retention_pass: true
wrong_history_gap_retention_pass: true
success_drop_count_retention_pass: true
gate_pass: true
```

Replay artifacts:

```text
runs/m1061_short61049_to_short61050_replay_sanity/summary.json
runs/m1061_short61049_to_short61051_replay_sanity/summary.json
runs/m1061_short61050_to_short61049_replay_sanity/summary.json
runs/m1061_short61050_to_short61051_replay_sanity/summary.json
runs/m1061_short61051_to_short61049_replay_sanity/summary.json
runs/m1061_short61051_to_short61050_replay_sanity/summary.json
```

## Classification

```text
result_class: post_short_promotion_family_intersection_corpus_pass
failure_types: none
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

This resolves the M1058 replay failure as a corpus selection issue rather than
an objective-sanity failure or actor-contract issue.

## Decision

```text
post_short_promotion_family_intersection_corpus_pass_route_to_synthesis
```

Next:

```text
m1062-v4-public-base-post-short-promotion-surface-refresh-synthesis
```

M1062 should synthesize M1054-M1061 before adding more narrow surface-refresh
steps. The main decision is whether the new family-intersection corpus should
be integrated as a refreshed public proof gate before medium PPO, or whether
the branch needs more mining.
