# M1564 Paper-Route Source-Balanced Selector Result Audit

## Summary

M1564 audits M1563.

Decision:

```text
source_balanced_selector_audit_admit_flip_anchor_source_generation_repair_design
```

M1563 is a clean selector implementation and should be kept. It fixes the raw
M1560 source/window concentration problem for a diagnostic subset, but it does
not produce a materializable active set for history interventions because the
distinct flip-anchor gates fail.

Failure taxonomy:

```text
scenario_sampling_failure
```

The next step should be a source-generation repair design that targets
source-diverse distinct flip anchors. It should not reinterpret local variant
counts as independent anchors and should not route directly to history
interventions.

## M1563 Evidence

Selector-quality gates that passed:

```text
input_recoverable_boundary_anchor_count: 86
selected_recoverable_anchor_count: 40
selected_strong_recoverable_anchor_count: 27
selected_predecision_anchor_count: 37
selected_source_family_count: 5
selected_window_count: 5
max_selected_source_family_share: 0.3
max_selected_window_share: 0.3
guardrail_violation_count: 0
```

Selected source-family counts:

```text
curved_boundary_obstacle: 1
late_reveal_boundary: 4
t5_boundary_axis_retarget: 12
t5_high_speed_close_obstacle: 11
t5_near_boundary_warmup: 12
```

Selected window counts:

```text
decision: 3
decision_minus_16: 12
decision_minus_24: 12
reveal: 10
reveal_plus_4: 3
```

This means the source-balanced selector repaired the original raw-pool
concentration blocker:

```text
M1560 max_single_active_family_share: 0.45348837209302323
M1563 max_selected_source_family_share: 0.3
```

## Flip-Anchor Blocker

The failed gates are:

```text
input_flip_anchor_gate_infeasible
selected_collision_flip_anchor_count
selected_success_flip_anchor_count
```

The input pool itself has too few distinct flip anchors:

```text
input_collision_flip_anchor_count: 5
input_success_flip_anchor_count: 5
required: 8 each
```

The selected set necessarily has the same limit:

```text
selected_collision_flip_anchor_count: 5
selected_success_flip_anchor_count: 5
```

All selected flip anchors come from one source family:

```text
collision flip anchor families:
t5_boundary_axis_retarget: 5

success flip anchor families:
t5_boundary_axis_retarget: 5
```

Their windows are also concentrated:

```text
decision_minus_24: 2
decision_minus_16: 2
reveal: 1
```

The variant counts are larger:

```text
selected_collision_flip_variant_count: 30
selected_success_flip_variant_count: 30
```

But these are repeated local-hold variants on only five anchors. Treating them
as 30 independent active-set anchors would weaken the source-diversity standard
and create a public-gate overfitting risk.

## Interpretation

M1563 should be classified as:

```text
selector implementation: pass
source/window balance: pass
strong/predecision coverage: pass
guardrails: pass
distinct flip-anchor coverage: fail
materialization readiness: fail
history-intervention readiness: fail
```

This is not a self-identification result. M1563 does not run wrong-history,
reset-history, delayed-history, or donor-history interventions. It only selects
local-control-sensitive recoverable anchors.

The scientific blocker is now narrower:

```text
the current recoverable active-set pool has enough recoverable anchors but not
enough source-diverse distinct anchors where local holds flip success/collision.
```

## Route Decision

Admit a design-only repair milestone:

```text
m1565-paper-route-flip-anchor-source-generation-repair-design
```

The repair should target more distinct flip anchors by changing source
generation and local-hold search, not by changing the actor input contract or
running history interventions.

M1565 should design a bounded generator repair with gates such as:

```text
distinct_collision_flip_anchor_count >= 8
distinct_success_flip_anchor_count >= 8
flip_anchor_source_family_count >= 3
flip_anchor_window_count >= 3
selected_recoverable_anchor_count >= 40
selected_strong_recoverable_anchor_count >= 24
guardrail_violation_count == 0
```

The route should remain no-training and no-materialization until the repaired
source generation is implemented and audited.

## Guardrails

```text
simulator_rerun_started: false in M1563 selector
history_interventions_executed: false
candidate_materialized: false
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1565-paper-route-flip-anchor-source-generation-repair-design
```
