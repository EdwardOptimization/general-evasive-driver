# M1299 Paper-Route Source-History Trainable-Scope Probe

## Summary

M1299 implements and runs the bounded no-PPO source-history trainable-scope
diagnostic designed in M1298.

Decision:

```text
source_history_trainable_scope_strong_route_to_result_audit
```

Result class:

```text
source_history_trainable_scope_strong
```

This is the first strong diagnostic result in the post-M1297 branch: allowing
`response_context_fusion + actor_mean` to train makes the fixed source-history
hidden-state signal substantially more directional than actor_mean-only probes.

This is still not a driver-performance result, not PPO readiness, not checkpoint
promotion, and not closed-loop self-identification proof.

## Command

Focused test:

```bash
PYTHONPATH=src python -m pytest -q \
  tests/test_source_history_trainable_scope_probe.py
```

Result:

```text
1 passed in 1.51s
```

Probe:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_history_trainable_scope_probe \
  --checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --history-run-dir runs/m1280_four_wheel_source_response_history_materialization \
  --intervention-run-dir runs/m1277_four_wheel_source_intervention_materialization \
  --run-dir runs/m1299_source_history_trainable_scope_probe \
  --device cpu \
  --steps 400 \
  --lr 0.0002 \
  --target-margin 0.05
```

## Implementation

Added:

```text
src/autodrift/source_history_trainable_scope_probe.py
tests/test_source_history_trainable_scope_probe.py
```

The probe:

```text
loads the M1280/M1277 source-history corpus;
creates a deterministic pair-disjoint public train/eval split;
trains small no-PPO candidates by allowed parameter scope;
reports full/train/eval row and group directional metrics;
reports parameter-group deltas and forbidden mutation flags;
writes diagnostic checkpoints only;
does not run PPO or promote.
```

Public split:

```text
full_row_count: 152
train_row_count: 120
eval_row_count: 32
train_pair_count: 30
eval_pair_count: 8
pair_split_disjoint: true
```

This is a public split for diagnostic discipline, not a private holdout.

## Result

Best scope:

```text
best_scope: fusion_head
best_scope_class: trainable_scope_directional_strong
best_eval_group_all_rows_both_positive_fraction: 0.25
best_eval_both_directional_fraction: 0.25
best_full_group_all_rows_both_positive_count: 23
best_full_both_positive_count: 46
forbidden_parameter_mutation_detected: false
```

Scope comparison:

```text
actor_mean_only_replay:
  full_both_positive_count: 24/152
  full_group_all_rows_both_positive_count: 12/76
  eval_both_directional_fraction: 0.125
  eval_group_all_rows_both_positive_fraction: 0.125
  scope_class: trainable_scope_directional_negative

fusion_head:
  full_both_positive_count: 46/152
  full_group_all_rows_both_positive_count: 23/76
  eval_both_directional_fraction: 0.25
  eval_group_all_rows_both_positive_fraction: 0.25
  scope_class: trainable_scope_directional_strong

current_step_gru_fusion_head:
  full_both_positive_count: 42/152
  full_group_all_rows_both_positive_count: 21/76
  eval_both_directional_fraction: 0.25
  eval_group_all_rows_both_positive_fraction: 0.25
  scope_class: trainable_scope_directional_strong
```

Compared with M1295:

```text
M1295 best full both-positive rows: 30/152
M1299 fusion_head full both-positive rows: 46/152

M1295 best all-rows-both-positive groups: 15/76
M1299 fusion_head all-rows-both-positive groups: 23/76
```

## Mutation Guard

`fusion_head` allowed:

```text
actor_mean
response_context_fusion
```

Observed deltas:

```text
actor_mean_l2: 0.0708169483
response_context_fusion_l2: 1.7883674671
online_gru_cell_l2: 0.0
response_encoder_l2: 0.0
context_encoder_l2: 0.0
critic_l2: 0.0
log_std_l2: 0.0
sequence_tail_l2: 0.0
privileged_l2: 0.0
other_l2: 0.0
```

`current_step_gru_fusion_head` allowed:

```text
actor_mean
response_context_fusion
online_gru_cell
```

It also preserved forbidden groups. No scope reported forbidden mutation.

## Interpretation

Supported:

```text
The actor_mean-only branch was underpowered. The fixed source-history hidden
states contain more useful directional information than actor_mean-only probes
could decode.
```

Supported:

```text
The first useful widened scope is fusion_head. Training online_gru_cell in
addition is not necessary for the best diagnostic result in this run.
```

Supported:

```text
The pair-disjoint public eval split does not collapse to zero: fusion_head and
current_step_gru_fusion_head both reach 0.25 eval row/group fractions.
```

Caveat:

```text
The eval thresholds are met exactly at 0.25, not with slack. This should be
audited and repeated before any proof-retention or PPO-admission design.
```

Not supported:

```text
Checkpoint promotion.
```

Not supported:

```text
PPO continuation readiness.
```

Not supported:

```text
Closed-loop driver performance or self-identification proof.
```

## Guardrails

M1299 preserved:

```text
labels_enter_actor_input: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
forbidden_parameter_mutation_detected: false
```

## Next Step

Pre-register:

```text
m1300-paper-route-source-history-trainable-scope-result-audit
```

M1300 should audit this as a strong diagnostic but boundary-threshold result,
then decide whether to repeat `fusion_head`, design proof-retention gates, or
refresh corpus before any PPO.
