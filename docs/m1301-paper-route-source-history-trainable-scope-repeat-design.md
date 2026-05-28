# M1301 Paper-Route Source-History Trainable-Scope Repeat Design

## Summary

M1301 designs a repeat/split robustness probe for the M1299 `fusion_head`
source-history signal.

Decision:

```text
source_history_trainable_scope_repeat_design_admit_bounded_repeat_probe
```

M1299 is a strong diagnostic result, but M1300 identified that the public eval
thresholds are met exactly at `0.25`. The next experiment should test whether
the `fusion_head` result survives deterministic pair-disjoint split variants.

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
threshold relaxation, high-fidelity validation claim, paper-level claim, or
self-identification claim occurs in M1301.

## Repeat Scope

Primary scope:

```text
fusion_head
```

Allowed parameter groups:

```text
actor_mean
response_context_fusion
```

Blocked parameter groups:

```text
online_gru_cell
response_encoder
context_encoder
critic
log_std
sequence_tail
privileged modules
other parameters
```

Reason:

```text
M1299 found fusion_head is the best scope. current_step_gru_fusion_head also
met the threshold, but it changed more parameters and did not improve the best
full-corpus metrics over fusion_head.
```

## Split Variants

M1302 should extend the M1299 probe with deterministic split offsets:

```text
split_mod: 5
split_offsets: 0, 1, 2, 3, 4
eval if stable_hash(pair_id) % split_mod == split_offset
train otherwise
```

Each variant must be pair-disjoint:

```text
train_pair_ids intersect eval_pair_ids == empty
```

Required per-variant reports:

```text
split_offset
train_pair_count
eval_pair_count
train_row_count
eval_row_count
full_both_positive_count
full_group_all_rows_both_positive_count
eval_both_directional_fraction
eval_group_all_rows_both_positive_fraction
forbidden_parameter_mutation_detected
```

## Training Recipe

Use the same M1299 objective and starting checkpoint:

```text
checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
scope: fusion_head
steps: 400
lr: 0.0002
target_margin: 0.05
lambda_group_floor: 4.0
lambda_group_balance: 0.5
lambda_anchor: 0.001
```

This is still no-PPO supervised diagnostic optimization on public source-history
rows.

## Pass/Fail Criteria

Per-offset pass:

```text
eval_both_directional_fraction >= 0.25
eval_group_all_rows_both_positive_fraction >= 0.25
full_both_positive_count > 30
full_group_all_rows_both_positive_count > 15
forbidden_parameter_mutation_detected == false
```

Repeat strong:

```text
offset_pass_count >= 3/5
mean_eval_both_directional_fraction >= 0.25
mean_eval_group_all_rows_both_positive_fraction >= 0.25
mean_full_both_positive_count > 30
mean_full_group_all_rows_both_positive_count > 15
forbidden_parameter_mutation_detected == false for every offset
```

Repeat mixed:

```text
at least one offset passes, but repeat strong is false
```

Repeat negative:

```text
no offset passes
```

Contract artifact:

```text
any forbidden parameter group changes
```

## Required Artifacts

M1302 should write:

```text
runs/m1302_source_history_trainable_scope_repeat_probe/summary.json
runs/m1302_source_history_trainable_scope_repeat_probe/repeat_summaries.csv
runs/m1302_source_history_trainable_scope_repeat_probe/split_rows.csv
runs/m1302_source_history_trainable_scope_repeat_probe/directional_rows.csv
runs/m1302_source_history_trainable_scope_repeat_probe/group_rows.csv
runs/m1302_source_history_trainable_scope_repeat_probe/parameter_group_delta.csv
runs/m1302_source_history_trainable_scope_repeat_probe/train_trace.csv
```

Focused tests should cover:

```text
multiple split offsets are pair-disjoint;
repeat summary aggregates offset pass counts;
forbidden parameter mutation is detected;
PPO/private-holdout/promotion flags remain false.
```

## Interpretation

If repeat strong:

```text
Route to result audit, then design proof-retention/replay gates before PPO.
```

If repeat mixed:

```text
Route to result audit and decide whether to tune the trainable-scope objective
or refresh the source-history corpus.
```

If repeat negative:

```text
Route to result audit and pivot toward source-history corpus refresh or
sequence/trajectory preference targets.
```

If contract artifact:

```text
Repair tooling before rerun.
```

## Guardrails

M1301 preserves:

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
m1302-paper-route-source-history-trainable-scope-repeat-probe
```

PPO and promotion remain blocked.
