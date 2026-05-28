# M1298 Paper-Route Source-History Trainable-Scope Escalation Design

## Summary

M1298 designs the first branch after M1297 closed actor_mean-only objective work
as underpowered.

Decision:

```text
source_history_trainable_scope_design_admit_bounded_no_ppo_probe
```

The next experiment should stay no-PPO and non-promotional. It should test
whether the source-history directional gate remains mixed because only
`actor_mean` was trainable, or whether the corpus/objective itself is the
limiting factor.

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
threshold relaxation, high-fidelity validation claim, paper-level claim, or
self-identification claim occurs in M1298.

## Architecture Constraint

The current human-view online recurrent actor uses:

```text
response_obs -> response_encoder -> online_gru_cell -> next_hidden
context_obs  -> context_encoder
[next_hidden, context_encoded, next_hidden * context_encoded]
  -> response_context_fusion -> actor_mean
```

Existing source-history objective batches hold:

```text
current 72-value observation
correct hidden
wrong hidden
preferred action
rejected action
```

The hidden states are replayed from M1280 history prefixes and then detached in
the current M1288/M1292/M1295 tooling. Therefore, M1299 must not claim it is
training the prefix history encoder unless it explicitly implements
differentiable prefix replay.

## Trainable Scopes

M1299 should compare these scopes:

```text
scope=actor_mean_only_replay
  Reuse M1295 actor_mean-only metrics as the baseline, or rerun exactly for
  pipeline parity.

scope=fusion_head
  Train response_context_fusion + actor_mean.
  Freeze response_encoder, context_encoder, online_gru_cell, critic, log_std,
  sequence_tail, privileged modules, and all other parameters.

scope=current_step_gru_fusion_head
  Optional second diagnostic if fusion_head is finite.
  Train online_gru_cell + response_context_fusion + actor_mean.
  This tests current-step response integration, not differentiable prefix
  history learning.
```

Explicitly blocked in M1299:

```text
prefix_gru_training
response_encoder_training
context_encoder_training
critic/log_std/sequence_tail training
any PPO or rollout update
```

Reason:

```text
Those scopes need separate design because they either affect prefix-history
encoding, broader current-frame perception encoding, value/log-std behavior, or
closed-loop rollout dynamics.
```

## Split-Eval Discipline

M1299 must create a deterministic public split by source pair, not by row:

```text
split key: pair_id
train: source-diverse pair_id subset
eval: disjoint pair_id subset
```

Do not split the two rows of a pair/probe group across train and eval. Do not
split only by row index.

Suggested deterministic rule:

```text
eval if stable_hash(pair_id) % 5 == 0
train otherwise
```

Required reports:

```text
train_row_count
eval_row_count
train_group_count
eval_group_count
train_pair_count
eval_pair_count
full_corpus_metrics
train_split_metrics
eval_split_metrics
```

This is still a public diagnostic split, not a private holdout. It reduces
same-corpus overfitting risk but does not create unbiased paper evidence.

## Objective

Use the M1295 pair-group objective on the train split:

```text
L = L_correct + L_wrong
  + lambda_group_floor * group_floor
  + lambda_group_balance * group_balance
  + lambda_anchor * parameter_anchor
```

M1299 should preserve the M1295 target margin for comparability:

```text
target_margin = 0.05
```

Use small steps and conservative LR:

```text
steps: 300-500
lr: 1e-4 to 3e-4
```

The exact configuration should be pre-registered in M1299 before running.

## Mutation Guard

M1299 must report parameter deltas by group:

```text
actor_mean_l2
response_context_fusion_l2
online_gru_cell_l2
response_encoder_l2
context_encoder_l2
critic_l2
log_std_l2
sequence_tail_l2
other_l2
```

For each scope, all forbidden groups must have zero delta.

Forbidden mutation in any scope:

```text
actor input contract change
log_std change
critic change
sequence_tail change
privileged module change
checkpoint metadata shortcut
```

## Gates

M1299 is diagnostic infrastructure. It cannot promote.

Strong scope signal requires:

```text
eval_group_all_rows_both_positive_fraction >= 0.25
eval_both_directional_fraction >= 0.25
full_group_all_rows_both_positive_count > 15
full_both_positive_count > 30
forbidden_parameter_mutation_detected == false
```

Mixed scope signal:

```text
at least one allowed scope improves full_group_all_rows_both_positive_count or
full_both_positive_count over M1295, but eval thresholds are not met.
```

Negative scope signal:

```text
no allowed scope improves full-corpus directional metrics, or eval split
degrades, or forbidden mutation occurs.
```

## Required Artifacts

M1299 should write:

```text
runs/m1299_source_history_trainable_scope_probe/summary.json
runs/m1299_source_history_trainable_scope_probe/scope_summaries.csv
runs/m1299_source_history_trainable_scope_probe/split_rows.csv
runs/m1299_source_history_trainable_scope_probe/directional_rows.csv
runs/m1299_source_history_trainable_scope_probe/group_rows.csv
runs/m1299_source_history_trainable_scope_probe/parameter_group_delta.csv
runs/m1299_source_history_trainable_scope_probe/train_trace.csv
```

It should also add focused tests for:

```text
scope selection only mutates allowed parameter groups;
split is pair-disjoint;
summary reports full/train/eval metrics;
PPO/private-holdout/promotion flags remain false.
```

## Interpretation Rules

If `fusion_head` is strong:

```text
Route to result audit, then decide whether proof-retention gates can be
designed before any PPO.
```

If `fusion_head` is mixed and `current_step_gru_fusion_head` improves:

```text
Route to result audit and design a current-step GRU/fusion continuation with
stricter anchor and split-eval.
```

If all scopes remain mixed or negative:

```text
Route to result audit and pivot toward source-history corpus refresh or
sequence/trajectory preference targets.
```

If any forbidden mutation occurs:

```text
Reject the run as a contract artifact and repair tooling before rerunning.
```

## Guardrails

M1298 preserves:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
self_identification_claimed: false
```

## Next Step

Pre-register:

```text
m1299-paper-route-source-history-trainable-scope-probe
```

PPO and promotion remain blocked.
