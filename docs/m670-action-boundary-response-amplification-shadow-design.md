# M670 Action-Boundary Response-Amplification Shadow Design

## Purpose

M670 turns the M669 ladder into a concrete frozen-actor shadow objective. The
goal is to test whether frozen BC5660 feature views contain enough
history-conditioned information to support sustained action-sequence separation
when the actor itself is not mutated.

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
```

## Evidence Being Targeted

M667 showed:

```text
near_boundary_preferred_snapshots: 204
candidate_rows:                   9600
wrong_first_action_l2 >= 0.002:   8934
wrong_action_sequence_mean_l2 >= 0.006: 4
preferred/rejected mean_l2 >= 0.010:    0
margin_gap >= 0.010:                    0
success_drop_rate:                      0.000
```

So the current actor has first-action sensitivity to wrong history, but not
sustained sequence separation and not outcome sensitivity. M671 should test
whether this is an actor-head/fusion boundary issue that a shadow head can
diagnose, not whether the closed-loop driver is solved.

## Shadow Corpus

M671 should build a training-only shadow corpus from M667 candidate rows and
reconstructed simulator snapshots.

Inputs:

```text
checkpoint:
  runs/m568_scaled_l3_bc_seed5660/checkpoint.pt

candidate rows:
  runs/m667_normal_success_boundary_source_miner/candidate_scores.csv

surface configs:
  fresh=configs/ppo_m541_matched_l3_variance_4096.json
  ood=configs/eval_m574_moderate_ood_l3.json
```

Candidate filter:

```text
normal_success == true
wrong_success == true
normal_margin >= 0.0
normal_margin <= 1.0
wrong_first_action_l2 >= 0.002
sequence_length in {5, 7, 9}
```

Selection:

```text
sort by wrong_first_action_l2 descending,
then wrong_action_sequence_mean_l2 descending,
then context_distance ascending;
cap rows per physical_pair_key;
cap rows per left_seed;
cap total rows to keep compute bounded.
```

Initial implementation defaults:

```text
max_rows: 768
max_rows_per_physical_pair: 18
max_rows_per_left_seed: 36
source-heldout split: hold out whole physical_pair_key groups
```

## Reconstructed Fields

For each selected row, M671 should reconstruct:

```text
observation
normal_hidden
wrong_hidden
normal_action_sequence[K, 3]
wrong_action_sequence[K, 3]
sequence_mask[K]
source_index
physical_pair_key
surface
target
left_seed / right_seed
left_step / right_step
split
weight
```

It should also compute frozen actor feature views for normal and wrong hidden:

```text
fused
next_hidden
fused_plus_next_hidden
```

These feature views are training features for the shadow head only. They are
not new actor inputs.

## Target Construction

The shadow head predicts bounded action residual sequences:

```text
delta_sequence = head(feature_view)
predicted_action_sequence = normal_action_sequence + delta_sequence
```

Normal branch target:

```text
target_delta_normal = 0
```

Wrong branch target:

```text
base_delta = wrong_action_sequence - normal_action_sequence
amplified_delta = scale_to_min_gap(base_delta)
target_delta_wrong = clip(amplified_delta, abs_delta <= 0.03)
```

Initial target parameters:

```text
target_wrong_sequence_mean_l2: 0.012
max_abs_delta_per_action_dim: 0.030
min_base_direction_norm: 1e-6
```

If the base wrong-normal direction is too small or invalid, reject the row from
the shadow corpus rather than inventing an arbitrary direction.

## Shadow Model

Use a small trainable head while freezing the actor:

```text
ResponseAmplifierHead(feature_dim, hidden_dim=64, K, action_dim=3)
```

Architecture:

```text
Linear(feature_dim, hidden_dim)
Tanh
Linear(hidden_dim, hidden_dim)
Tanh
Linear(hidden_dim, K * 3)
reshape(K, 3)
```

Train one head per feature view:

```text
fused
next_hidden
fused_plus_next_hidden
```

Run at least three seeds:

```text
6700, 6701, 6702
```

## Loss

Per batch:

```text
L_normal_anchor =
  masked_mse(head(normal_feature), target_delta_normal)

L_wrong_target =
  masked_mse(head(wrong_feature), target_delta_wrong)

L_gap_margin =
  softplus(target_gap - masked_mean_l2(head(wrong_feature) - head(normal_feature)))

L_zero_regularizer =
  masked_mse(head(normal_feature), 0)

L_total =
  L_normal_anchor
  + wrong_target_coef * L_wrong_target
  + gap_margin_coef * L_gap_margin
  + zero_regularizer_coef * L_zero_regularizer
```

Initial coefficients:

```text
wrong_target_coef: 1.0
gap_margin_coef: 0.25
zero_regularizer_coef: 0.1
target_gap: 0.010
```

Normal preservation is first-class. A head that separates wrong history by
moving normal actions too much fails.

## Metrics

M671 should report row-level, source-level, split-level, and view/seed-level
metrics:

```text
normal_delta_l2_mean
normal_delta_l2_max
wrong_delta_l2_mean
predicted_normal_wrong_gap_l2_mean
predicted_normal_wrong_gap_l2_p10
baseline_actor_sequence_gap_l2_mean
gap_improvement_ratio
normal_anchor_mse
wrong_target_mse
source-heldout versions of all of the above
```

The exact evaluator in M671 must compute full-corpus metrics after training;
training loss alone is not enough.

## Pass Criteria

A view/seed passes only if source-heldout validation satisfies:

```text
normal_delta_l2_mean <= 0.0025
normal_delta_l2_p95 <= 0.0060
predicted_normal_wrong_gap_l2_mean >= 0.010
predicted_normal_wrong_gap_l2_p10 >= 0.004
gap_improvement_ratio >= 3.0
wrong_target_mse improves over zero-head baseline by >= 50%
```

The milestone passes only if:

```text
at least one non-fused view passes in >= 2/3 seeds
actor checksum unchanged
only shadow head checkpoints written
no actor checkpoint written
no PPO used
```

If fused passes but next-hidden does not, treat that as suspicious and audit
before actor coupling; the expected self-ID-relevant signal should be strongest
in next-hidden or fused-plus-next-hidden.

## Required Artifacts

M671 should write:

```text
runs/m671_response_amplification_shadow/summary.json
runs/m671_response_amplification_shadow/shadow_corpus_metadata.csv
runs/m671_response_amplification_shadow/shadow_corpus.npz
runs/m671_response_amplification_shadow/seed_view_summary.csv
runs/m671_response_amplification_shadow/row_metrics.csv
runs/m671_response_amplification_shadow/source_summary.csv
runs/m671_response_amplification_shadow/split_summary.csv
runs/m671_response_amplification_shadow/target_summary.csv
docs/m671-action-boundary-response-amplification-shadow-implementation.md
```

Shadow head checkpoints may be written under per-seed/per-view subdirectories.
Actor checkpoints must not be written.

## Negative Result Taxonomy

M671 should classify failures explicitly:

```text
normal_anchor_failure:
  normal branch residuals exceed retention thresholds.

wrong_sequence_gap_failure:
  normal branch is preserved, but wrong-history gap stays below threshold.

source_holdout_overfit:
  train passes but source-heldout fails.

feature_view_failure:
  all fused/next-hidden/fused-plus-hidden views fail.

corpus_reconstruction_failure:
  selected rows cannot be reconstructed or source-heldout split is empty.
```

## Forbidden Shortcuts

Do not:

- mutate actor parameters;
- write actor checkpoint;
- run PPO;
- use hidden parameters or labels as actor input;
- treat shadow-head success as closed-loop self-ID proof;
- skip source-heldout exact metrics.

## Decision

```text
response_amplification_shadow_design_admit_m671
```

## Next

```text
m671-action-boundary-response-amplification-shadow-implementation
```
