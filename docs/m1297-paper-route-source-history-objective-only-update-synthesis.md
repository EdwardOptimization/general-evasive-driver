# M1297 Paper-Route Source-History Objective-Only Update Synthesis

## Summary

M1297 synthesizes the `paper_route_source_history_objective_only_update` branch
from M1287 through M1296.

Synthesis decision:

```text
pivot
```

Decision:

```text
source_history_objective_only_update_synthesis_pivot_to_trainable_scope_escalation
```

The branch should close as an actor_mean-only objective branch. The evidence
shows that actor_mean-only optimization can move the source-history diagnostic
surface, but it cannot repair the directional gate strongly enough to admit PPO
or checkpoint promotion.

Open the next branch:

```text
paper_route_source_history_trainable_scope_escalation
```

No training, PPO, checkpoint promotion, private holdout, actor-input expansion,
threshold relaxation, high-fidelity validation claim, paper-level claim, or
self-identification claim occurs in M1297.

## Evidence Summary

M1287 designed the first objective-only update path:

```text
checkpoint: M1154 public-gate base
trainable scope: actor_mean only
objective: exact source-history correct/wrong preference loss
guardrail: no PPO, no promotion, no private holdout, no actor-input change
```

M1288 implemented the update and produced a strong exact-loss improvement:

```text
base_combined_loss_mean: 18.6105005714
after_combined_loss_mean: 7.1793530621
combined_loss_delta: -11.4311475093
trainable_parameter_count: 387
frozen_parameter_count: 164292
non_actor_mean_l2: 0.0
result_class: source_history_objective_update_exact_loss_improved
```

M1289 audited M1288 as exact-loss-positive but directional-gate weak.

M1290 diagnosed the branch failure mode:

```text
result_class: source_history_directional_conflict_magnitude_compression
after_both_directional_fraction: 0.0
after_both_positive_count: 0
after_mutually_exclusive_count: 152
loss_improved_count: 152
min_abs_margin_decreased_count: 152
```

M1291 rejected blind scalar-loss continuation and routed to a directional
feasibility probe.

M1292 ran the actor_mean directional feasibility probe:

```text
result_class: source_history_actor_mean_directional_feasibility_mixed
best_init_name: m1288_init
best_both_directional_fraction: 0.1842105263
best_both_positive_count: 28
best_mutually_exclusive_fraction: 0.7763157895
any_non_actor_mean_mutation_detected: false
```

M1293 audited M1292 as mixed and non-promotable.

M1294 designed a pair-group objective to prevent one row in a pair/probe group
from improving while the other remains wrong.

M1295 ran the pair-group objective probe:

```text
result_class: source_history_pair_group_objective_mixed
best_init_name: base_init
best_both_directional_fraction: 0.1973684211
best_both_positive_count: 30
best_mutually_exclusive_fraction: 0.6710526316
best_group_all_rows_both_positive_count: 15
best_group_all_rows_both_positive_fraction: 0.1973684211
any_non_actor_mean_mutation_detected: false
```

M1296 audited M1295 as valid infrastructure but below the strong gate:

```text
strong row threshold: 0.25
strong group threshold: 0.25
M1295 row fraction: 0.1973684211
M1295 group fraction: 0.1973684211
```

## Supported Claims

Supported:

```text
The source-history exact objective is measurable, finite, and trainable on the
current 152-row public diagnostic corpus.
```

Supported:

```text
Actor_mean-only optimization can reduce the exact preference loss without
mutating frozen parameters or violating the actor input contract.
```

Supported:

```text
Actor_mean-only directional objectives can recover a small number of
both-positive rows and groups.
```

Supported:

```text
The pair/probe group metric is useful. It prevents the branch from mistaking
row-level loss reduction for group-level source-history repair.
```

Supported:

```text
The research harness correctly prevented PPO admission after exact-loss
improvement failed to become directional evidence.
```

## Falsified Claims

Falsified:

```text
Exact combined loss improvement alone is enough to show source-history repair.
M1288 improved exact loss, but M1290 found 152/152 mutually exclusive rows.
```

Falsified:

```text
Actor_mean-only row-wise directional optimization can solve the source-history
gate. M1292 remained mixed at 28/152 both-positive rows.
```

Falsified:

```text
Actor_mean-only pair-group optimization can solve the source-history gate.
M1295 remained mixed at 15/76 all-rows-both-positive groups.
```

Falsified:

```text
The objective-only actor_mean branch is ready for PPO continuation or checkpoint
promotion.
```

Not yet proven:

```text
The source-history corpus itself is sufficient once a wider trainable policy
surface is allowed.
```

Not yet proven:

```text
A wider trainable scope can improve source-history directionality without
breaking existing public proof gates.
```

## Failure Taxonomy Summary

Primary scientific diagnosis:

```text
actor_mean_scope_underpowered
```

Nearest existing taxonomy labels:

```text
none
```

Reason:

```text
The branch did not fail as infrastructure, did not mutate forbidden parameters,
and did not regress a promoted checkpoint. It produced bounded negative/mixed
evidence that the actor_mean-only surface is too small for the intended
source-history directional repair.
```

Secondary risk:

```text
objective_overfit
```

Reason:

```text
M1288-M1296 repeatedly optimize and audit the same fixed public 152-row corpus.
Further narrow actor_mean-only edits would risk tuning to public diagnostics
without answering whether the policy architecture can actually use the
history-response signal.
```

## Public-Gate Overfit Risk

Risk:

```text
high
```

The branch repeatedly used the same source-history corpus:

```text
M1288 exact objective update
M1290 directional conflict audit
M1292 directional feasibility probe
M1295 pair-group objective probe
```

This is acceptable for debugging the objective, but not enough for a paper-level
claim. The next branch must separate:

```text
trainable-scope limitation
corpus/source limitation
objective formulation limitation
```

## Next Branch Decision

Close:

```text
paper_route_source_history_objective_only_update
```

Open:

```text
paper_route_source_history_trainable_scope_escalation
```

The next branch should not run PPO. It should first design a bounded no-PPO
trainable-scope diagnostic that asks:

```text
Can the same human-view source-history evidence become directional when the
policy decoder/fusion surface is allowed to adapt under strict guards?
```

Recommended first design task:

```text
m1298-paper-route-source-history-trainable-scope-escalation-design
```

M1298 should define:

```text
trainable scopes to compare;
exact objective and directional gates;
source-diverse train/eval split on the public corpus;
mutation reporting by parameter group;
no PPO, no promotion, no private holdout, no actor-input change.
```

The intended first implementation after design should be small and diagnostic:

```text
actor_mean_only baseline reused from M1295;
fusion_head scope: actor_mean + response_context_fusion;
optional current_step_gru_fusion scope if gradients remain bounded;
no differentiable prefix-GRU training until a separate design proves it is
needed and auditable.
```

## Guardrails

M1297 preserves:

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

The branch-level conclusion is:

```text
actor_mean-only objective work is exhausted for now.
```

The next branch should test trainable-scope sufficiency before refreshing the
source-history corpus or changing to a sequence/trajectory objective. If wider
scope also stays mixed, the next synthesis should pivot to source-history corpus
refresh or sequence preference targets.
