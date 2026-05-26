# M1012 V4 Public Base Margin-Weighted Branch Repair Update Design

## Purpose

M1012 designs the first repaired actor update after M1011 proves that
margin-slack weighting detects the known alpha `0.01` wrong-history branch
washout.

This is design-only. It does not train, optimize, run PPO, run replay gates,
use private holdout, change actor inputs, or promote a checkpoint.

## Baseline

Base checkpoint:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

Temporal objective corpus:

```text
runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz
```

Branch trust evaluator:

```text
runs/m1011_v4_public_base_margin_weighted_branch_trust_region_evaluator/summary.json
```

M1011 calibrated scale:

```text
M974 base trust loss: 0.0
M1002 alpha 0.01 trust loss: 3.529713744145817
M1002 alpha 0.20 trust loss: 1407.006193470631
alpha 0.01 primary contribution fraction: 0.6645155784636552
```

## Trainable Surface

M1013 should update only:

```text
actor_mean
```

It must freeze:

```text
response_encoder
context_encoder
online_gru_cell
response_context_fusion
critic
log_std
sequence_tail if present
all observation contracts
```

Reasoning:

```text
M1002 already showed actor_mean-only temporal exact movement is possible.
M1004 showed that the movement proof-washes M267/M264 rows 6 and 15.
M1013 should therefore test whether the same trainable surface can be repaired
by adding the M1011 branch trust residual before widening the actor.
```

## Loss

Use the M999/M1002 temporal objective:

```text
L_temporal =
  L_normal_nll
+ lambda_pref * L_temporal_pref
+ lambda_anchor * L_base_logp_anchor
```

with:

```text
lambda_pref = 1.0
lambda_anchor = 0.25
preference_margin = 0.05
```

Add the M1011 wrong-branch trust residual:

```text
L_wrong_branch_trust =
  mean_i normalized_source_weight_i *
    ||a_wrong_candidate_i - a_wrong_base_i||^2
    / max(abs(base_wrong_margin_i), margin_floor)^2
```

where:

```text
active rows: 6, 15, 11, 16
primary rows: 6, 15
secondary rows: 11, 16
source weights: primary 4.0, secondary 2.0
margin_floor: 1e-4
```

Full loss:

```text
L =
  L_temporal
+ lambda_wrong_trust * L_wrong_branch_trust
```

Initial coefficient sweep:

```text
lambda_wrong_trust in {0.001, 0.003, 0.01, 0.03}
```

Rationale:

```text
M1002 alpha 0.01 improved temporal total loss by about 0.001435 but had M1011
branch trust loss 3.529714. A coefficient of 0.001 already makes that known
proof-washing direction unattractive while still allowing the optimizer to find
directions that improve temporal exact metrics without moving active rejected
branches.
```

The branch trust term is a proof-retention constraint, not a deployable target.
Wrong-history rollouts should remain bad only as a counterfactual proof surface.
The deployed actor still sees only P0 human-view observations and online GRU
history.

## Optimization Plan

M1013 should run a deterministic objective-only probe:

```text
seed: 1013
epochs: 200
batching: full corpus for temporal rows, full active set for branch rows
optimizer: Adam
learning_rate: 1e-4
gradient_clip_norm: 1.0
trainable parameters: actor_mean only
```

For each `lambda_wrong_trust`, save:

```text
raw updated checkpoint
interpolated checkpoints
train history
exact temporal metrics
M1011 branch trust metrics
changed parameter names
```

Interpolation grid:

```text
0.0025
0.005
0.010
0.020
0.050
0.100
0.200
0.500
1.000
```

The raw update is only a direction. Candidate selection happens by exact
metrics over interpolated checkpoints.

## Candidate Gates

M1013 may admit a candidate only if all exact temporal gates pass:

```text
weighted_total_loss <= base_weighted_total_loss - 0.001
weighted_normal_sequence_nll <= base_weighted_normal_sequence_nll + 0.005
weighted_temporal_preference_loss <= base_weighted_temporal_preference_loss + 0.005
weighted_logp_gap_mean >= base_weighted_logp_gap_mean - 0.050
temporal_logp_gap_p10 >= base_temporal_logp_gap_p10 - 0.020
candidate_action_l2_mean <= 0.015
candidate_action_l2_max <= 0.080
actor_parameters_changed == true only for actor_mean
training_started == true
ppo_used == false
promoted == false
```

Then require branch trust retention:

```text
weighted_branch_trust_loss <= 0.10
primary_weighted_branch_trust_loss <= 0.07
max_weighted_row_contribution <= 0.05
row 6 contribution <= 0.05
row 15 contribution <= 0.02
row 16 contribution <= 0.05
```

These thresholds are intentionally much tighter than the known failing
M1002 alpha `0.01` direction:

```text
alpha 0.01 weighted_branch_trust_loss: 3.529714
alpha 0.01 row 6 contribution: 1.745044
alpha 0.01 row 15 contribution: 0.600505
alpha 0.01 row 16 contribution: 0.989614
```

If no candidate passes these thresholds, M1013 should classify the failure as
`objective_overfit` or `proof_washout` depending on whether temporal exact
progress or branch retention is the blocker. It should not relax thresholds and
claim success in the same milestone.

## Replay Order After M1013

M1013 itself should not run the full public replay stack. If exact/trust
candidates exist, the next milestone should run:

```text
1. M267/M264 full preflight over candidate alphas
2. selected candidate exact temporal retention
3. six public replay surfaces
4. source-diverse protected diagnostics
5. behavior seeds 9505 and 9506
6. only then decide whether a later promotion/generalization protocol is needed
```

Private holdout remains unused.

## Blocked Routes

Do not:

```text
run PPO;
promote;
change actor inputs;
train GRU or encoders;
use hidden dynamics or oracle labels;
train variant histories toward degraded actions;
use diagnostic cross-fault rows as positive targets;
use private holdout;
relax branch trust thresholds inside the same implementation milestone.
```

## Decision

```text
margin_weighted_branch_repair_update_design_admit_m1013_probe
```

Next:

```text
m1013-v4-public-base-margin-weighted-branch-repair-update-probe
```
