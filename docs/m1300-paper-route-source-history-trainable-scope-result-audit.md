# M1300 Paper-Route Source-History Trainable-Scope Result Audit

## Summary

M1300 audits the M1299 trainable-scope probe.

Decision:

```text
source_history_trainable_scope_audit_strong_route_to_repeat_design
```

M1299 is accepted as a strong diagnostic result, but not as a promotion or PPO
admission result. The key reason is that the public eval split thresholds are
met exactly at `0.25`, so the next step should test repeat/split robustness
before proof-retention or PPO design.

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
threshold relaxation, high-fidelity validation claim, paper-level claim, or
self-identification claim occurs in M1300.

## Evidence

M1299 result:

```text
result_class: source_history_trainable_scope_strong
best_scope: fusion_head
best_scope_class: trainable_scope_directional_strong
train_row_count: 120
eval_row_count: 32
train_pair_count: 30
eval_pair_count: 8
pair_split_disjoint: true
forbidden_parameter_mutation_detected: false
```

Best `fusion_head` metrics:

```text
full_both_positive_count: 46/152
full_group_all_rows_both_positive_count: 23/76
eval_both_directional_fraction: 0.25
eval_group_all_rows_both_positive_fraction: 0.25
```

Comparison to M1295:

```text
M1295 best full both-positive rows: 30/152
M1299 fusion_head full both-positive rows: 46/152

M1295 best full all-rows-both-positive groups: 15/76
M1299 fusion_head full all-rows-both-positive groups: 23/76
```

Scope comparison:

```text
actor_mean_only_replay:
  full_both_positive_count: 24/152
  full_group_all_rows_both_positive_count: 12/76
  eval fractions: 0.125 row, 0.125 group
  scope_class: trainable_scope_directional_negative

fusion_head:
  full_both_positive_count: 46/152
  full_group_all_rows_both_positive_count: 23/76
  eval fractions: 0.25 row, 0.25 group
  scope_class: trainable_scope_directional_strong

current_step_gru_fusion_head:
  full_both_positive_count: 42/152
  full_group_all_rows_both_positive_count: 21/76
  eval fractions: 0.25 row, 0.25 group
  scope_class: trainable_scope_directional_strong
```

## Supported Claims

Supported:

```text
Actor_mean-only was underpowered for this source-history diagnostic.
```

Supported:

```text
Training `response_context_fusion + actor_mean` makes the fixed source-history
hidden-state signal materially more directional on the public diagnostic corpus.
```

Supported:

```text
The useful first widened scope is `fusion_head`; adding `online_gru_cell` is not
necessary for the best M1299 result.
```

Supported:

```text
The mutation guard is clean. For `fusion_head`, only `actor_mean` and
`response_context_fusion` changed.
```

## Falsified Claims

Falsified:

```text
The source-history diagnostic failure was caused only by a bad corpus or target.
M1299 shows the same corpus becomes substantially more directional with a wider
decoder/fusion scope.
```

Falsified:

```text
Actor_mean-only continuation is the right next local repair path.
```

Not yet proven:

```text
The M1299 strong diagnostic is robust across split offsets or fresh repeat
variants.
```

Not yet proven:

```text
The `fusion_head` candidate preserves older public proof gates or improves
closed-loop behavior.
```

Not yet proven:

```text
The result supports PPO continuation.
```

## Caveats

Boundary threshold:

```text
eval_both_directional_fraction: 0.25
eval_group_all_rows_both_positive_fraction: 0.25
```

The result meets the pre-registered threshold but has no eval slack. This makes
it a strong diagnostic signal, not yet a robust base.

Public split:

```text
The train/eval split is public and deterministic. It reduces same-row overfit
risk but is not a private holdout.
```

Fixed-current diagnostic:

```text
M1299 still evaluates fixed intervention observations with replayed hidden
states. It is not a closed-loop driver test and not self-identification proof.
```

## Public-Gate Overfit Risk

Risk:

```text
moderate
```

The split discipline improved over M1288-M1296, but the eval set is small:

```text
eval pairs: 8
eval rows: 32
eval groups: 16
```

One additional eval group would move the fraction materially. Therefore M1300
routes to repeat/split robustness before any proof-retention or PPO design.

## Next Routing

Next:

```text
m1301-paper-route-source-history-trainable-scope-repeat-design
```

M1301 should design a repeat/split robustness probe:

```text
scope: fusion_head only, unless audit explicitly includes current_step_gru_fusion_head
split variants: multiple pair-disjoint deterministic split offsets
same target margin and objective
same mutation guard
no PPO
no promotion
no private holdout
```

Suggested pass condition:

```text
at least 2/3 split variants meet eval row/group threshold >= 0.25;
mean full_group_all_rows_both_positive_count remains > 15;
forbidden mutation remains false for all repeats.
```

## Guardrails

M1300 preserves:

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

## Decision

M1299 is a meaningful positive diagnostic result. The project should not
dismiss it as noise, but it should also not jump to PPO.

The next correct move is repeat/split robustness.
