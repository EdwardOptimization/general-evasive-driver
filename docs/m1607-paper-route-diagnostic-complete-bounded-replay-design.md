# M1607 Paper-Route Diagnostic-Complete Bounded Replay Design

## Summary

M1607 designs the diagnostic-complete replay admitted by M1606.

Decision:

```text
diagnostic_complete_bounded_replay_design_route_to_branch_synthesis_before_implementation
```

The next implementation should reuse the M1605 replay runner with a label-blind
diagnostic-complete configuration. It should not select diagnostics by M1602
labels, should not change actor inputs, and should still route to audit before
any materialization or training decision.

The workflow synthesis cadence has fired for the current
`paper_route_clean_active_set_contour_mapping` branch, so this design cannot
route directly to implementation. M1608 must first synthesize M1598-M1607 and
then decide whether the configured diagnostic-complete implementation remains
admissible.

## Inputs

Primary source:

```text
runs/m1602_contour_aware_source_rule/primary_rule_rows.csv
```

Diagnostic source:

```text
runs/m1602_contour_aware_source_rule/diagnostic_rule_rows.csv
```

Replay selection:

```text
primary rows: all 144 rows
diagnostic rows: all 232 rows
selection rule: rule_reason only
label-based selection: forbidden
```

The diagnostic reason counts are:

```text
endpoint_neighbor_exclusion: 120
negative_diagnostic_edge: 64
mixed_dominated_edge: 48
```

The implementation can achieve this with:

```text
--diagnostic-per-reason-cap 999
```

This is not a threshold relaxation. It removes the M1605 diagnostic sampling cap
and replays the full diagnostic set.

## Expected Scale

```text
primary_replay_directed_pair_count: 144
diagnostic_replay_directed_pair_count: 232
total_replay_directed_pair_count: 376
variant_count: 8
expected_intervention_row_count: 3008
```

## Public Gates

M1608 should pass only if:

```text
primary_replay_directed_pair_count >= 144
diagnostic_replay_directed_pair_count >= 232
diagnostic_reason_count >= 3
primary_source_run_count >= 2
primary_source_edge_count == 4
primary_clean_directed_pair_count >= 39
primary_clean_source_edge_count >= 4
max_primary_clean_source_edge_share <= 0.35
endpoint_neighbor_primary_count == 0
negative_diagnostic_primary_count == 0
mixed_diagnostic_primary_count == 0
diagnostic_dominated_or_control_count >= 75
diagnostic_clean_share <= 0.02
required_variant_coverage_complete == true
anchor_replay_failure_count <= 8
guardrail_violation_count == 0
history_interventions_executed == true
replay_started == true
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

## Required Artifacts

M1608 should write:

```text
runs/m1608_diagnostic_complete_bounded_replay/summary.json
runs/m1608_diagnostic_complete_bounded_replay/replay_pair_rows.csv
runs/m1608_diagnostic_complete_bounded_replay/intervention_rows.csv
runs/m1608_diagnostic_complete_bounded_replay/classified_directed_pair_rows.csv
runs/m1608_diagnostic_complete_bounded_replay/primary_classified_rows.csv
runs/m1608_diagnostic_complete_bounded_replay/diagnostic_classified_rows.csv
runs/m1608_diagnostic_complete_bounded_replay/primary_source_edge_summary.csv
runs/m1608_diagnostic_complete_bounded_replay/diagnostic_rule_reason_summary.csv
runs/m1608_diagnostic_complete_bounded_replay/variant_summary.csv
runs/m1608_diagnostic_complete_bounded_replay/guardrail_summary.csv
```

## Failure Taxonomy

Use:

```text
diagnostic_complete_bounded_replay_public_pass:
  primary contour is preserved and full diagnostics preserve negative/control evidence.

primary_clean_shortfall:
  primary replay no longer preserves 39 clean rows.

diagnostic_control_failure:
  full diagnostic replay still has dominated/control count below 75.

diagnostic_clean_leakage:
  full diagnostic clean share exceeds 0.02.

variant_coverage_failure:
  one or more required intervention variants is missing.

anchor_replay_failure:
  too many target/donor anchor replays fail.

guardrail_violation:
  candidate materialization, corpus export, training, PPO, promotion, private
  holdout, actor-input change, label selection, or self-ID overclaim occurs.
```

## Route Decision

Route to mandatory branch synthesis before implementation:

```text
m1608-paper-route-clean-active-set-contour-mapping-branch-synthesis
```

If synthesis continues the branch, the follow-up implementation should use the
configured full diagnostic replay. If synthesis pivots or stops, do not run the
implementation.

## Guardrails

```text
replay_started: false in M1607
history_interventions_executed: false in M1607
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
m1608-paper-route-clean-active-set-contour-mapping-branch-synthesis
```
