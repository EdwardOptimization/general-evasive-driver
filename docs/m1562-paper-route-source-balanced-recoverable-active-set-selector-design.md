# M1562 Paper-Route Source-Balanced Recoverable Active-Set Selector Design

## Summary

M1562 designs a diagnostic-only source-balanced selector over the M1560
recoverable active-set pool.

Decision:

```text
source_balanced_recoverable_active_set_selector_design_admit_bounded_selector
```

The selector does not rerun the simulator and does not run history
interventions. It only reads M1560 public artifacts and selects a compact,
source/window-balanced recoverable active-set diagnostic subset.

## Inputs

M1563 should read:

```text
runs/m1560_recoverable_active_set_generator_smoke/recoverable_active_anchor_rows.csv
runs/m1560_recoverable_active_set_generator_smoke/local_hold_rows.csv
runs/m1560_recoverable_active_set_generator_smoke/summary.json
```

It should not read private holdout data, checkpoints beyond the M1560 lineage,
or any oracle labels not already present as public diagnostic artifacts.

## Selection Policy

Candidate rows:

```text
recoverable_boundary == true
```

Ranking priority:

```text
strong_recoverable_boundary first;
collision_flip_count descending;
success_flip_count descending;
max_abs_terminal_margin_gap descending;
predecision anchors before decision anchors;
source-family rarity bonus;
window rarity bonus.
```

Hard caps:

```text
max_per_source_family: 12
max_per_anchor_window: 12
max_selected_rows: 48
```

Diagnostics retained but not selected:

```text
already_colliding
high_margin_safe
inactive_boundary
replay_failed
```

## M1563 Gates

M1563 should pass public selector gates only if:

```text
input_recoverable_boundary_anchor_count >= 80
selected_recoverable_anchor_count >= 40
selected_strong_recoverable_anchor_count >= 24
selected_predecision_anchor_count >= 32
selected_source_family_count >= 5
selected_window_count >= 5
max_selected_source_family_share <= 0.30
max_selected_window_share <= 0.35
selected_collision_flip_anchor_count >= 8
selected_success_flip_anchor_count >= 8
guardrail_violation_count == 0
history_interventions_executed == false
simulator_rerun_started == false
training_corpus_exported == false
```

Evidence-quality targets:

```text
selected_recoverable_anchor_count >= 45
selected_strong_recoverable_anchor_count >= 28
max_selected_source_family_share <= 0.28
max_selected_window_share <= 0.32
selected_source_family_count == 5
selected_window_count == 5
```

## Required Artifacts

M1563 should write:

```text
runs/m1563_source_balanced_recoverable_active_set_selector/selected_active_anchor_rows.csv
runs/m1563_source_balanced_recoverable_active_set_selector/rejected_active_anchor_rows.csv
runs/m1563_source_balanced_recoverable_active_set_selector/selector_source_family_summary.csv
runs/m1563_source_balanced_recoverable_active_set_selector/selector_window_summary.csv
runs/m1563_source_balanced_recoverable_active_set_selector/selector_guardrail_summary.csv
runs/m1563_source_balanced_recoverable_active_set_selector/summary.json
```

Do not write:

```text
history intervention rows;
training corpus;
checkpoint;
promotion artifact.
```

## Follow-Up Logic

If M1563 passes:

```text
M1564 audits the selected diagnostic active set.
Only after that audit may a later milestone design history interventions over
the selected rows.
```

If M1563 fails:

```text
M1564 audits whether source balancing is impossible from M1560 artifacts or
whether the selector gates need a source-generation repair.
```

## Guardrails

```text
simulator_rerun_started: false
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
m1563-paper-route-source-balanced-recoverable-active-set-selector-implementation
```
