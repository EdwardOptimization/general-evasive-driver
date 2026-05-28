# M1347 Paper-Route Materialized Source-History Pair-Group Update Result Audit

## Summary

M1347 audits the M1346 bounded no-PPO pair-group update before any replay gate,
PPO, promotion, or larger update.

Decision:

```text
materialized_source_history_pair_group_update_audit_admit_limited_replay_preflight
```

This remains a public fixed-objective audit. It does not promote the M1346
candidate and does not claim driver performance or strong self-identification.

## M1346 Result Recap

M1346 candidate:

```text
runs/m1346_materialized_source_history_pair_group_update/checkpoints/raw_pair_group_update.pt
```

Mutation and contract guard:

```text
checkpoint_contract: canonical_72_human_view_online_recurrent
trainable_scope: response_context_fusion_plus_actor_mean
forbidden_parameter_mutation_detected: false
log_std_l2: 0.0
actor_input_contract_changed: false
```

Exact row objective:

```text
combined_loss_mean: 6.8847534022 -> 1.9998926339
delta: -4.8848607683
```

Exact group objective:

```text
group_min_joint_margin_mean: -6.8026667906 -> -1.1251848645
delta: +5.6774819261
```

Eval fold 4:

```text
group_min_joint_margin_mean: -6.4443958161 -> -1.2625397266
delta: +5.1818560896
```

Directional group counts:

```text
one_sided_conflict: 684 -> 605
all_rows_both_directional: 0 -> 27
both_negative: 4 -> 26
```

## Transition Audit

Group state transitions:

```text
both_negative -> both_negative: 4
one_sided_conflict -> both_directional: 27
one_sided_conflict -> both_negative: 22
one_sided_conflict -> one_sided_conflict: 605
one_sided_conflict -> other: 30
```

The `other` groups are partial directional groups:

```text
c+_w+:1;c+_w-:1 = 20
c-_w+:1;c-_w-:1 = 7
c+_w+:1;c-_w+:1 = 3
```

Both-negative groups after M1346 by family:

```text
left_right_split_mu: 2
single_wheel_brake_pull: 8
single_wheel_grip_collapse: 4
steering_actuator_fault: 10
tire_blowout_like: 2
load_cg_perturbation: 0
```

Both-directional groups after M1346 by family:

```text
left_right_split_mu: 16
load_cg_perturbation: 1
single_wheel_grip_collapse: 8
tire_blowout_like: 2
single_wheel_brake_pull: 0
steering_actuator_fault: 0
```

By fold:

```text
fold 0: both_negative 5, both_directional 6
fold 1: both_negative 5, both_directional 6
fold 2: both_negative 8, both_directional 5
fold 3: both_negative 4, both_directional 7
fold 4: both_negative 4, both_directional 3
```

This is not a singleton artifact. The both-negative increase is distributed
across folds and concentrated most strongly in steering actuator and single
wheel brake pull families. It is still small relative to the full surface:

```text
both_negative_after: 26 / 688 = 3.78%
both_directional_after: 27 / 688 = 3.92%
one_sided_conflict_after: 605 / 688 = 87.94%
```

## Interpretation

Supported:

```text
M1346 is a valid bounded objective update: exact row loss, full group-min
margin, and eval-fold group-min margin all improve without forbidden mutation.
```

Supported:

```text
The pair-group objective changes directionality in the intended direction for a
nonzero subset of groups: 27 groups become all-rows-both-directional.
```

Supported:

```text
The update does not merely compress all signs uniformly; it also creates a
tradeoff where 22 one-sided groups become both-negative.
```

Not supported:

```text
M1346 solved the source-history directionality surface.
```

Not supported:

```text
M1346 should become a promoted base without replay gates.
```

Not supported:

```text
M1346 proves closed-loop self-identification or driver performance.
```

## Risk Classification

Failure taxonomy:

```text
objective_overfit:
  fixed public source-history objective improved, but replay/proof gates remain
  unevaluated.
```

Tradeoff:

```text
directionality_tradeoff:
  27 one-sided groups become both-directional while 22 one-sided groups become
  both-negative.
```

No evidence of:

```text
contract_violation
forbidden_parameter_mutation
private_holdout_contamination
training_instability
promotion_gate_failure
```

## Decision

M1346 is healthy enough for a limited public replay preflight because:

```text
1. exact full-corpus group-min margin improves strongly;
2. eval fold 4 improves instead of regressing;
3. one-sided conflicts decrease;
4. no forbidden parameters mutate;
5. no private holdout, PPO, promotion, or actor-input change occurred.
```

M1346 is not healthy enough for promotion because:

```text
1. only 27 / 688 groups become all-rows-both-directional;
2. both-negative groups increase from 4 to 26;
3. all evidence is still fixed public source-current diagnostic evidence;
4. closed-loop public replay gates have not been run.
```

Next route:

```text
m1348-paper-route-materialized-source-history-pair-group-limited-replay-preflight
```

M1348 should evaluate the M1346 candidate against a limited public replay stack
and behavior guard, compare it to the M1154 base, and stop before promotion.
If replay gates fail, route to objective tradeoff repair design rather than PPO.
