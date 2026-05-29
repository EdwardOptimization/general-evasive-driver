# M1561 Paper-Route Recoverable Active-Set Generator Result Audit

## Summary

M1561 audits M1560.

Decision:

```text
recoverable_active_set_generator_audit_admit_source_balanced_selector_design
```

M1560 is a strong generator result but not a materializable active set. The
branch now has enough recoverable anchors, strong recoverable anchors, source
families, windows, success flips, and collision flips. The remaining blocker is
active source-family concentration.

Failure taxonomy:

```text
scenario_sampling_failure
```

The next step should be a source-balanced selector design, not history
interventions.

## M1560 Evidence

```text
recoverable_boundary_anchor_count: 86
strong_recoverable_boundary_anchor_count: 36
predecision_recoverable_anchor_count: 80
active_source_family_count: 5
active_window_count: 5
success_flip_count: 66
collision_flip_count: 30
guardrail_violation_count: 0
```

These counts clear the main recoverability objective from M1559.

The failing public gate is concentration:

```text
max_single_active_family_share: 0.45348837209302323
threshold: 0.35
```

Recoverable anchors by source family:

```text
t5_near_boundary_warmup: 39
t5_boundary_axis_retarget: 19
t5_high_speed_close_obstacle: 18
late_reveal_boundary: 9
curved_boundary_obstacle: 1
```

Strong recoverable anchors by source family:

```text
t5_near_boundary_warmup: 15
t5_boundary_axis_retarget: 14
t5_high_speed_close_obstacle: 5
late_reveal_boundary: 2
```

## Selector Feasibility

A source-balanced selector is feasible from the existing public pool. A simple
cap of `12` recoverable anchors per source family yields:

```text
selected recoverable anchors: 46
selected strong recoverable anchors: 31
selected families: 5
max selected family share: 0.2608695652173913
```

This suggests the problem is not lack of data. It is that M1560 reported the
raw generated pool directly instead of selecting a balanced active set for later
diagnostics.

## Interpretation

M1560 should not be treated as history-necessity evidence. It did not run
wrong-history, reset-history, delayed-history, or hidden-state interventions.

M1560 does support a narrower claim:

```text
multi-step local holds can expose a sizeable pool of recoverable active-set
anchors in the current public simulator.
```

The blocker is now evidence governance:

```text
choose a source-balanced recoverable subset before any history intervention.
```

## Route Decision

Admit a design-only milestone:

```text
m1562-paper-route-source-balanced-recoverable-active-set-selector-design
```

M1562 should design a selector that:

```text
uses only M1560 public artifacts;
does not rerun simulator;
does not run history interventions;
does not export a training corpus;
caps source-family and window concentration;
prioritizes strong recoverable anchors;
keeps enough weak recoverable anchors for source/window diversity;
keeps already_colliding and high_margin_safe rows as diagnostics only.
```

If the selector design is clean, a later implementation may produce a compact
balanced active-set audit artifact. History interventions remain blocked until
that selected set passes and is audited.

## Guardrails

```text
history_interventions_executed: false
candidate_materialized: false
training_started: false
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
m1562-paper-route-source-balanced-recoverable-active-set-selector-design
```
