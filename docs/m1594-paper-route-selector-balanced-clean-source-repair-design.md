# M1594 Paper-Route Selector-Balanced Clean-Source Repair Design

## Summary

M1594 designs the threshold-preserving selector-balanced cap repair admitted by
M1593.

Decision:

```text
selector_balanced_clean_source_repair_design_admit_bounded_implementation
```

M1594 does not treat M1592 as a pass. It preserves the clean selector thresholds
and the `0.35` max clean source-edge share gate. The next implementation may
only change the pair-selection balance rule before replay; it may not relax any
evidence gate.

## M1592 Blocker

M1592 improved the clean surface but failed source concentration:

```text
clean_directed_pair_count: 34
clean_source_edge_count: 5
clean_endpoint_source_family_count: 6
max_clean_source_edge_share: 0.35294117647058826
gate: <= 0.35
invalid_directed_pair_count: 0
```

The largest clean edge was:

```text
actuator_delay_step|capability_step_up: 12 clean rows
```

The miss is narrow, but post-hoc threshold relaxation is not allowed.

## Design Change

M1592 used a per-source-edge selected-pair cap of `16`, which allowed the clean
surface to become slightly concentrated. M1595 should use a stricter and more
explicit source-balanced selection rule:

```text
target selected pairs: 96
max selected pairs per source edge: 12
minimum selected source edges: 8
source-edge round-robin selection: true
source seed: 1901
max source specs: 480
max anchor candidates: 640
continuation steps: 64
```

The repair should still prioritize clean evidence in this order:

```text
1. clean edge + clean window
2. clean edge
3. negative diagnostic edge
4. clean endpoint neighbor
5. fallback pairable edge
```

But within that priority, selection should be source-edge balanced. It should
not fill one source edge to cap before giving other eligible source edges a
chance.

## Preserved Clean Selector

The clean label remains:

```text
history_control_separated
```

with unchanged criteria:

```text
history_max_gap >= 0.02
control_max_gap < 0.75 * history_max_gap
hidden_specific_gap >= 0.01
```

The max clean source-edge share gate remains:

```text
max_clean_source_edge_share <= 0.35
```

## Implementation Gates

M1595 should pass only if:

```text
source_spec_count >= 360
selected_pair_count >= 96
selected_source_edge_count >= 8
classified_directed_pair_count >= 128
required_variant_coverage_complete == true
invalid_directed_pair_count == 0
clean_directed_pair_count >= 12
clean_source_edge_count >= 5
clean_endpoint_source_family_count >= 6
max_clean_source_edge_share <= 0.35
guardrail_violation_count == 0
candidate_materialized == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
training_corpus_exported == false
labels_enter_actor_input == false
level3_self_id_claim_made == false
```

M1595 must route to audit whether it passes or fails.

## Negative Diagnostics

M1595 must continue to report:

```text
history_positive_control_dominated
control_only_positive
history_null_all_controls_null
```

The dominated/control-only rows are not noise. They are the guardrail that keeps
the branch from counting current-frame/action-history substitution as clean
history evidence.

## Not Allowed

M1594 does not admit:

```text
candidate materialization;
training corpus export;
PPO;
promotion;
private holdout;
actor-input changes;
clean selector threshold relaxation;
max clean source-edge share threshold relaxation;
level3 self-identification claims.
```

## Route Decision

Admit exactly one bounded implementation:

```text
m1595-paper-route-selector-balanced-clean-source-repair-implementation
```

If M1595 fails, route to audit before any further repair. If it passes, route to
audit before materialization or any training decision.

## Guardrails

```text
history_interventions_executed: false in M1594
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
m1595-paper-route-selector-balanced-clean-source-repair-implementation
```
