# M1563 Paper-Route Source-Balanced Recoverable Active-Set Selector Implementation

## Summary

M1563 implements and runs the diagnostic-only selector designed in M1562.

Decision:

```text
source_balanced_recoverable_active_set_selector_clean_but_flip_anchor_gate_infeasible_route_to_audit
```

The selector itself is clean: it reads only M1560 public artifacts, does not
rerun the simulator, does not run history interventions, and does not export a
training corpus. It produces a compact source/window-balanced recoverable
active-set subset.

The public selector gate still fails because the pre-registered flip-anchor
requirements are infeasible from the M1560 input pool:

```text
input_collision_flip_anchor_count: 5
input_success_flip_anchor_count: 5
required: 8 each
```

M1564 must audit whether this is a gate-design mismatch or a real source
generation gap before any history-intervention design.

## Implementation

Added:

```text
src/autodrift/source_balanced_recoverable_active_set_selector.py
tests/test_source_balanced_recoverable_active_set_selector.py
```

The selector:

```text
loads M1560 recoverable_active_anchor_rows.csv;
loads M1560 local_hold_rows.csv for selected-local diagnostics;
filters recoverable_boundary == true;
prioritizes strong recoverable anchors, flip counts, margin gap, predecision
windows, source rarity, and window rarity;
enforces max_per_source_family = 12;
enforces max_per_anchor_window = 12;
selects a compact diagnostic set targeting the public minimum count;
writes selected/rejected rows, source/window summaries, guardrail summary, and
summary.json.
```

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_source_balanced_recoverable_active_set_selector.py -q
3 passed
```

Smoke command:

```text
PYTHONPATH=src python -m autodrift.source_balanced_recoverable_active_set_selector \
  --output-dir runs/m1563_source_balanced_recoverable_active_set_selector \
  --input-dir runs/m1560_recoverable_active_set_generator_smoke
```

## Result

```text
input_recoverable_boundary_anchor_count: 86
input_strong_recoverable_boundary_anchor_count: 36
input_collision_flip_anchor_count: 5
input_success_flip_anchor_count: 5
input_collision_flip_variant_count: 30
input_success_flip_variant_count: 30
selected_recoverable_anchor_count: 40
selected_strong_recoverable_anchor_count: 27
selected_predecision_anchor_count: 37
selected_source_family_count: 5
selected_window_count: 5
max_selected_source_family_share: 0.3
max_selected_window_share: 0.3
selected_collision_flip_anchor_count: 5
selected_success_flip_anchor_count: 5
selected_collision_flip_variant_count: 30
selected_success_flip_variant_count: 30
input_flip_anchor_gate_feasible: false
passes_public_selector_gates: false
passes_evidence_quality_targets: false
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

Failed public selector gates:

```text
input_flip_anchor_gate_infeasible
selected_collision_flip_anchor_count
selected_success_flip_anchor_count
```

## Interpretation

M1563 fixes the source/window concentration problem for a diagnostic subset:

```text
selected_recoverable_anchor_count >= 40
selected_strong_recoverable_anchor_count >= 24
selected_predecision_anchor_count >= 32
selected_source_family_count >= 5
selected_window_count >= 5
max_selected_source_family_share <= 0.30
max_selected_window_share <= 0.35
```

But M1563 also reveals that the flip-anchor gate is not satisfiable under a
literal anchor-count interpretation using the M1560 pool. The input has enough
flip variants (`30` collision and `30` success local-hold variants), but only
`5` distinct collision-flip anchors and `5` distinct success-flip anchors.

This is not history-necessity evidence and not a materialization result. It is
a process result: source-balanced active-set selection works, but the next audit
must decide whether to repair source generation toward more distinct flip
anchors or revise the selector gate semantics in a pre-registered way.

## Guardrails

```text
simulator_rerun_started: false
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
m1564-paper-route-source-balanced-selector-result-audit
```

M1564 should audit M1563 before any further implementation. The likely decision
is either a source-generation repair for more distinct flip anchors, or a
carefully documented gate-semantics correction if the branch only needs variant
counts for the next diagnostic stage.
