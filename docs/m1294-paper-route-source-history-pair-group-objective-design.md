# M1294 Paper-Route Source-History Pair-Group Objective Design

## Summary

M1294 designs a pair-group directional objective after M1292 showed mixed
actor_mean feasibility.

Decision:

```text
source_history_pair_group_objective_design_admit_bounded_actor_mean_implementation
```

The next step should implement a bounded no-PPO actor_mean-only pair-group
objective probe:

```text
m1295-paper-route-source-history-pair-group-objective-probe
```

## Blocker

M1292 improved over the M1290 zero-both-positive state, but not enough:

```text
best_both_directional_fraction: 0.1842105263
best_both_positive_count: 28 / 152
best_mutually_exclusive_fraction: 0.7763157895
```

Group-level audit of M1292 rows:

```text
pair_probe_group_count: 76
base_init all-rows-both-positive groups: 12 / 76
m1288_init all-rows-both-positive groups: 14 / 76
```

Interpretation:

```text
Actor_mean-only has partial signal, but row-wise optimization still leaves most
two-row pair/probe groups unresolved.
```

## Objective Design

For each row:

```text
c_i = correct_preference_margin
w_i = wrong_history_preference_margin
r_i = min(c_i, w_i)
```

For each pair/probe group `g` with two rows:

```text
R_g = min(r_i for i in g)
B_g = mean((r_i - mean(r_g))^2 for i in g)
```

Pair-group objective:

```text
L_row =
  mean(softplus(target_margin - c_i))
+ mean(softplus(target_margin - w_i))

L_group_floor =
  mean(softplus(target_margin - R_g))

L_group_balance =
  mean(B_g)

L_anchor =
  ||actor_mean - actor_mean_base||^2

L_total =
  L_row
+ lambda_group_floor * L_group_floor
+ lambda_group_balance * L_group_balance
+ lambda_anchor * L_anchor
```

Suggested defaults:

```text
target_margin: 0.05
lambda_group_floor: 4.0
lambda_group_balance: 0.5
lambda_anchor: 0.001
steps: 500
learning_rate: 0.0003
initializations: base_init, m1288_init
```

## Why This Differs From M1292

M1292 optimized row-wise directional feasibility and reported row metrics. M1294
requires M1295 to treat the two rows in a `pair_id/probe_template` group as a
single unit.

This prevents the update from looking useful when:

```text
one row in a pair becomes both-positive;
the paired row remains mutually exclusive;
the aggregate both_positive count rises but the pair remains unresolved.
```

## M1295 Metrics

M1295 should report both row-level and group-level metrics.

Row-level:

```text
both_directional_fraction
both_positive_count
mutually_exclusive_fraction
min_margin_mean
min_margin_p10
```

Group-level:

```text
pair_probe_group_count
group_all_rows_both_positive_count
group_all_rows_both_positive_fraction
group_any_row_both_positive_count
group_any_row_both_positive_fraction
group_min_margin_mean
group_min_margin_p10
group_balance_loss_mean
```

Mutation:

```text
non_actor_mean_mutation_detected
actor_mean_l2_from_base
actor_mean_max_abs_from_base
```

## M1295 Pass/Fail Gates

Strong positive actor_mean pair-group signal:

```text
group_all_rows_both_positive_fraction >= 0.25
and both_directional_fraction >= 0.25
and group_all_rows_both_positive_count > 14
and non_actor_mean_mutation_detected == false
```

Mixed signal:

```text
group_all_rows_both_positive_count > 14
but strong positive thresholds are not met
```

Negative/capacity-limited signal:

```text
group_all_rows_both_positive_count <= 14
and both_directional_fraction <= 0.1842105263
```

If strong:

```text
route to result audit, then exact public proof-retention design.
```

If mixed:

```text
route to result audit and decide between scope escalation and source-history
surface refresh.
```

If negative:

```text
route to trainable-scope escalation design or corpus relabel/refresh audit.
```

## Implementation Scope

M1295 should remain bounded:

```text
trainable_scope: actor_mean_only
PPO: disabled
promotion: disabled
private_holdout: disabled
actor_input_change: forbidden
```

It may write diagnostic checkpoints for each initialization, but those
checkpoints are not promotable.

## Guardrails

M1295 must not:

```text
run PPO;
promote a checkpoint;
use private holdout;
add source/fault/condition/pair/probe labels to actor input;
update GRU, encoders, fusion, critic, log_std, or sequence-tail parameters;
claim closed-loop driver improvement;
claim paper-level evidence;
claim level3 self-identification.
```

## Claim Discipline

M1294 supports only:

```text
A bounded pair-group objective design exists for testing whether actor_mean-only
can improve two-row source-history pair/probe groups.
```

M1294 does not support:

```text
pair-group repair success;
PPO readiness;
promotion;
closed-loop driver improvement;
paper-level generalization;
strong self-identification.
```

PPO and promotion remain blocked.
