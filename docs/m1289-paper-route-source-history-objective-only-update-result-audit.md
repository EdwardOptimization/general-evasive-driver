# M1289 Paper-Route Source-History Objective-Only Update Result Audit

## Summary

M1289 audits the M1288 actor-mean-only objective update.

Decision:

```text
source_history_objective_update_audit_exact_loss_positive_directional_weak_admit_conflict_audit
```

M1288 is a valid exact objective-level positive result:

```text
combined_loss_mean: 18.6105005714 -> 7.1793530621
combined_loss_delta: -11.4311475093
non_actor_mean_mutation_detected: false
ppo_used: false
promoted: false
```

But M1288 is not a positive policy-side source-history gate:

```text
both_directional_fraction: 0.0 -> 0.0
preferred_hidden_margin_positive_fraction: 0.4868421053 -> 0.4078947368
```

Therefore M1289 routes to a row-wise directional conflict audit, not PPO, not
replay-gate escalation, and not checkpoint promotion.

## Exact-Loss Evidence

M1288 satisfies the M1287 exact-loss-first gate:

```text
row_count: 152
finite_before: true
finite_after: true
base_combined_loss_mean: 18.6105005714
after_combined_loss_mean: 7.1793530621
combined_loss_delta: -11.4311475093
base_correct_preference_loss_mean: 9.3052502857
after_correct_preference_loss_mean: 3.5896765310
correct_preference_loss_delta: -5.7155737547
base_wrong_history_preference_loss_mean: 9.3052502857
after_wrong_history_preference_loss_mean: 3.5896765310
wrong_history_preference_loss_delta: -5.7155737547
```

The training trace is monotonic enough for a tiny probe:

```text
step 96 loss: 7.7444291115
step 97 loss: 7.6313300133
step 98 loss: 7.5182719231
step 99 loss: 7.4052543640
step 100 loss: 7.2922821045
```

Interpretation:

```text
The objective is connected to the actor and can be reduced by changing only the
final action-mean head. This validates the update path mechanically.
```

## Mutation Guardrail

M1288 satisfies the mutation guardrail:

```text
trainable_scope: actor_mean_only
trainable_parameter_count: 387
frozen_parameter_count: 164292
actor_mean_changed: true
actor_mean_l2: 0.1133155453
actor_mean_max_abs: 0.0100500062
non_actor_mean_mutation_detected: false
non_actor_mean_l2: 0.0
non_actor_mean_max_abs: 0.0
```

This means the residual reduction came from the final action head, not from
hidden-state, encoder, critic, log-std, or observation-contract changes.

## Directional Caveat

The same artifacts also show the update did not solve row-wise directionality.

Before M1288:

```text
correct positive, wrong positive: 0
correct positive, wrong negative: 76
correct negative, wrong positive: 76
correct negative, wrong negative: 0
```

After M1288:

```text
correct positive, wrong positive: 0
correct positive, wrong negative: 76
correct negative, wrong positive: 76
correct negative, wrong negative: 0
```

So every row still has only one side of the desired relation correct. The exact
loss got smaller mostly by reducing large residual magnitudes:

```text
before combined_loss p50: 21.0526559845
after combined_loss p50: 7.6391813900
before min/max correct margin: -25.5421638489 / 25.9494113922
after min/max correct margin: -12.5033164024 / 13.0493540764
```

Interpretation:

```text
Exact loss improvement is necessary evidence that the objective is trainable,
but it is not sufficient evidence that correct histories now select preferred
actions and wrong histories select rejected actions row by row.
```

## Failure Taxonomy

Not observed:

```text
contract_violation:
  actor input contract stayed canonical 72-value human-view recurrent.
```

Not observed:

```text
training_instability:
  the tiny update ran and produced finite before/after exact objective metrics.
```

Not observed:

```text
proof_washout:
  public replay gates were intentionally not run because M1288 is not yet past
  the directional policy-gate stage.
```

Active:

```text
objective_overfit / directional_conflict:
  the public 152-row exact objective can be reduced while both_directional_fraction
  remains 0.0. This may be row-pair symmetry, actor_mean-only capacity limit,
  objective shape, or corpus conflict. It must be diagnosed before more update
  pressure or PPO.
```

Active:

```text
public_gate_overfit_risk:
  the same 152 public rows have now been used for evaluator design and one
  objective update. Do not use this corpus alone for a paper-level claim.
```

## Decision

Do not promote:

```text
M1288 raw_objective_update.pt is diagnostic only.
```

Do not run PPO:

```text
The policy-side directional gate remains weak.
```

Do not run old public replay gates yet:

```text
They would test retention before the new source-history relation is actually
positive.
```

Next:

```text
m1290-paper-route-source-history-directional-conflict-audit
```

M1290 should quantify whether the M1288 result is:

```text
a pure magnitude-compression update;
a row-pair sign-conflict artifact;
an actor_mean_only capacity limit;
or evidence that the objective needs row-wise directional repair.
```

## Claim Discipline

M1289 supports:

```text
The exact source-history objective can be reduced by a tiny actor-mean-only
no-PPO update without forbidden parameter mutation.
```

M1289 does not support:

```text
positive policy-side source-history gate;
closed-loop driver improvement;
promotion;
PPO readiness;
paper-level generalization;
level3 anticipatory self-identification.
```

PPO and promotion remain blocked.
