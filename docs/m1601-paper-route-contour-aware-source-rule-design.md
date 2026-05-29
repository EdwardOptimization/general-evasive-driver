# M1601 Paper-Route Contour-Aware Source Rule Design

## Summary

M1601 designs the contour-aware source rule admitted by M1600.

Decision:

```text
contour_aware_source_rule_design_admit_offline_selector_implementation
```

The next step should implement an offline source-rule selector only. It should
not replay, rerun the simulator, materialize candidates, export a training
corpus, train, run PPO, promote, or use private holdout.

## Evidence Basis

M1599 mapped `528` existing public directed pairs and found `51` clean rows.
The useful contour is not broad pairability. It is concentrated in
`clean_edge_window` rows.

The key selection-source facts are:

```text
clean_edge_window:
  144 rows, 39 clean rows, 4 primary source edges

clean_edge:
  16 rows, 3 clean rows

clean_endpoint_neighbor:
  120 rows, 0 clean rows, 19 control-only rows, 101 null rows

negative_diagnostic_edge:
  104 rows, 0-2 clean rows depending on source edge, dominated/control-heavy
```

The M1595 broad round-robin failure is explained by over-expansion into
`clean_endpoint_neighbor` and `negative_diagnostic_edge`. The rule must avoid
repeating that expansion.

## Primary Rule

Primary inclusion is deliberately narrow:

```text
selection_source == clean_edge_window
source_edge in:
  actuator_delay_step|capability_step_up
  curved_boundary_obstacle|t5_boundary_axis_retarget
  actuator_delay_step|t5_near_boundary_warmup
  capability_step_down|t5_near_boundary_warmup
```

This yields the current public contour:

```text
primary_rule_directed_pair_count: 144
primary_clean_directed_pair_count: 39
primary_clean_source_edge_count: 4
max_primary_clean_source_edge_share: 0.3333333333333333
endpoint_neighbor_primary_count: 0
```

The max clean source-edge share gate remains:

```text
max_primary_clean_source_edge_share <= 0.35
```

M1601 does not relax the clean selector thresholds:

```text
history_max_gap >= 0.02
control_max_gap < 0.75 * history_max_gap
hidden_specific_gap >= 0.01
```

## Diagnostic Rule

Diagnostic rows are required but must not be counted as primary clean evidence.

Mixed diagnostic edge:

```text
capability_step_up|t5_near_boundary_warmup
```

This edge has a small clean signal but is dominated-heavy:

```text
2 clean / 48 rows
22 dominated / 48 rows
```

Negative diagnostic selection sources:

```text
selection_source == negative_diagnostic_edge
```

Endpoint-neighbor rows:

```text
selection_source == clean_endpoint_neighbor
```

These rows are exclusion diagnostics. They show where broad source expansion
turns into control-only/null behavior. They must not enter the primary rule.

## Offline Implementation Gates

M1602 should pass only if:

```text
input_contour_row_count >= 528
primary_rule_directed_pair_count >= 144
primary_source_edge_count == 4
primary_clean_directed_pair_count >= 39
primary_clean_source_edge_count >= 4
max_primary_clean_source_edge_share <= 0.35
endpoint_neighbor_primary_count == 0
negative_diagnostic_primary_count == 0
mixed_diagnostic_primary_count == 0
diagnostic_directed_pair_count >= 150
diagnostic_dominated_or_control_count >= 50
guardrail_violation_count == 0
replay_started == false
history_interventions_executed == false
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

M1602 should write:

```text
runs/m1602_contour_aware_source_rule/summary.json
runs/m1602_contour_aware_source_rule/primary_rule_rows.csv
runs/m1602_contour_aware_source_rule/diagnostic_rule_rows.csv
runs/m1602_contour_aware_source_rule/excluded_rule_rows.csv
runs/m1602_contour_aware_source_rule/source_rule_summary.csv
runs/m1602_contour_aware_source_rule/guardrail_summary.csv
```

These are diagnostic/source-rule artifacts, not a training corpus.

## Null Taxonomy

Use:

```text
contour_aware_source_rule_public_pass:
  offline selector reproduces the primary contour and diagnostic exclusions.

primary_clean_shortfall:
  primary clean count falls below 39.

source_share_failure:
  primary clean source-edge share exceeds 0.35.

diagnostic_missing:
  dominated/control-only diagnostic exclusions are absent.

endpoint_neighbor_leakage:
  endpoint-neighbor rows enter the primary rule.

guardrail_violation:
  replay, simulator rerun, materialization, corpus export, training, PPO,
  promotion, private holdout, actor-input change, or self-ID overclaim occurs.
```

## Route Decision

Admit one offline implementation:

```text
m1602-paper-route-contour-aware-source-rule-implementation
```

If M1602 passes, route to audit before replay or materialization. If it fails,
audit before changing the rule. Do not immediately run replay.

## Guardrails

```text
replay_started: false
history_interventions_executed: false in M1601
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
m1602-paper-route-contour-aware-source-rule-implementation
```
