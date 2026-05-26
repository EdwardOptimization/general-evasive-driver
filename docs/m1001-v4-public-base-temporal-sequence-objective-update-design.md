# M1001 V4 Public Base Temporal Sequence Objective Update Design

## Purpose

M1001 designs the first objective-only actor update after M1000 exact evaluator
sanity passes.

This milestone does not train, optimize, run PPO, promote a checkpoint, or
change actor inputs. It only defines the M1002 implementation boundary.

## Baseline

Checkpoint:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

Corpus:

```text
runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz
```

M1000 baseline metrics:

```text
weighted_normal_sequence_nll: -1.373014
weighted_temporal_preference_loss: 0.491601
weighted_logp_gap_mean: 0.640106
weighted_total_loss: -0.881413
temporal_logp_gap_p10: 0.053981
normal_action_replay_l2_max: 0.0
```

## Trainable Surface

M1002 should update only:

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
The first update should test whether the existing representation already
contains enough temporal-history signal. If actor_mean-only cannot improve the
exact objective without collapsing the gap, widening the trainable surface
requires a separate audit.
```

## Loss

Use the M999 objective exactly:

```text
L = L_normal_nll
  + lambda_pref * L_temporal_pref
  + lambda_anchor * L_base_logp_anchor
```

Initial coefficients:

```text
lambda_pref = 1.0
lambda_anchor = 0.25
preference_margin = 0.05
```

Rows must use M997 `row_weight`.

The update must never train:

```text
variant hidden -> degraded variant action sequence
diagnostic cross-fault rows -> positive targets
```

## Optimization Plan

M1002 should run a small exact objective-only probe:

```text
epochs: 200
batch: full corpus or deterministic mini-batches with fixed seed
optimizer: Adam
learning_rate: 1e-4
gradient_clip_norm: 1.0
seed: 1002
```

Save:

```text
base checkpoint copy
raw updated checkpoint
interpolated checkpoints
```

Interpolation grid:

```text
0.005
0.010
0.020
0.050
0.100
0.200
0.500
1.000
```

The raw update is only a direction. Candidate selection should happen by exact
metrics over interpolated checkpoints.

## Exact Candidate Gates

M1002 may admit a candidate only if all exact gates pass:

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

`candidate_action_l2_*` should compare deterministic normal-history actions
from the candidate against the stored M997 normal actions on the normal rollout
observations. Unlike M1000 replay sanity, these values are allowed to be
nonzero; the thresholds are the exact trust region.

## Public Replay Is Not Part Of M1002

M1002 should not run full public replay gates. It should only decide whether an
exact objective-level candidate exists.

If an exact candidate exists, route to:

```text
M1003 public replay gate design
```

If no exact candidate exists, route to:

```text
objective update audit
```

The first actor update must not directly promote a checkpoint.

## Required Diagnostics

M1002 should report:

```text
trainable_parameter_names
changed_parameter_names
base exact metrics
raw exact metrics
alpha exact metrics
best alpha by weighted_total_loss among gate-passing candidates
action drift summary
gap quantiles
loss curves
```

Classify failures explicitly:

```text
objective_overfit:
  total loss improves but temporal gap or normal retention fails

proof_washout:
  exact candidate later fails replay/proof gates

training_instability:
  non-finite loss/grad or exploding action drift

promotion_gate_failure:
  no alpha passes exact gates
```

## Blocked Routes

Do not:

```text
run PPO;
run full public replay before exact candidate selection;
promote;
update GRU or encoders;
train variant histories toward degraded actions;
use diagnostic cross-fault rows as positives;
use private holdout;
change actor inputs.
```

## Decision

```text
temporal_sequence_update_design_admit_exact_probe
```

Next:

```text
m1002-v4-public-base-temporal-sequence-objective-update-probe
```
