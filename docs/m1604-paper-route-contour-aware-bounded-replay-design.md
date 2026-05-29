# M1604 Paper-Route Contour-Aware Bounded Replay Design

## Summary

M1604 designs the bounded replay admitted by M1603.

Decision:

```text
contour_aware_bounded_replay_design_admit_one_implementation
```

M1604 is design-only. It does not run replay. The next implementation may replay
only the pre-registered M1602 primary rows plus bounded diagnostic controls, and
it must route to audit before any materialization or training decision.

## Inputs

Primary replay source:

```text
runs/m1602_contour_aware_source_rule/primary_rule_rows.csv
```

Diagnostic replay source:

```text
runs/m1602_contour_aware_source_rule/diagnostic_rule_rows.csv
```

The implementation must use the directed fields already present in these rows:

```text
pair_id
target_anchor_id
donor_anchor_id
target_source_family
donor_source_family
target_anchor_window
donor_anchor_window
target_anchor_step
donor_anchor_step
same_window
step_distance
rule_bucket
rule_reason
```

It should not convert back through broad undirected pairability selection. The
point is to test the M1602 contour-aware rule, not regenerate a new source set.

## Replay Scope

Primary replay:

```text
use all 144 M1602 primary directed rows
primary rows must have rule_reason == clean_edge_window_primary
primary rows must have selection_source == clean_edge_window
endpoint-neighbor, negative-diagnostic, and mixed-dominated rows cannot enter primary replay
```

Diagnostic replay:

```text
sample up to 96 diagnostic directed rows
include at least 24 endpoint_neighbor_exclusion rows
include at least 24 negative_diagnostic_edge rows
include at least 24 mixed_dominated_edge rows
report diagnostics separately from primary
```

The diagnostic cap keeps runtime bounded while preserving the negative evidence.

## Variants

Use the same history/control intervention families as the current pairability
intervention branch:

```text
normal
wrong_history_hidden
donor_response_action_plus_hidden
donor_response_action_only
reset_hidden
zero_current_response
zero_action_history
zero_all_response
```

The classifier remains unchanged:

```text
history_control_separated
history_positive_control_dominated
control_only_positive
history_null_all_controls_null
replay_or_metric_invalid
```

## Public Gates

M1605 should pass only if:

```text
primary_replay_directed_pair_count >= 144
diagnostic_replay_directed_pair_count >= 72
diagnostic_reason_count >= 3
primary_source_run_count >= 2
primary_source_edge_count == 4
primary_clean_directed_pair_count >= 39
primary_clean_source_edge_count >= 4
max_primary_clean_source_edge_share <= 0.35
endpoint_neighbor_primary_count == 0
negative_diagnostic_primary_count == 0
mixed_diagnostic_primary_count == 0
diagnostic_dominated_or_control_count >= 50
diagnostic_clean_share <= 0.05
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

M1605 may start replay and history interventions. It may not materialize a
candidate, export a training corpus, train, run PPO, or promote.

## Required Artifacts

M1605 should write:

```text
runs/m1605_contour_aware_bounded_replay/summary.json
runs/m1605_contour_aware_bounded_replay/replay_pair_rows.csv
runs/m1605_contour_aware_bounded_replay/intervention_rows.csv
runs/m1605_contour_aware_bounded_replay/classified_directed_pair_rows.csv
runs/m1605_contour_aware_bounded_replay/primary_classified_rows.csv
runs/m1605_contour_aware_bounded_replay/diagnostic_classified_rows.csv
runs/m1605_contour_aware_bounded_replay/primary_source_edge_summary.csv
runs/m1605_contour_aware_bounded_replay/diagnostic_rule_reason_summary.csv
runs/m1605_contour_aware_bounded_replay/variant_summary.csv
runs/m1605_contour_aware_bounded_replay/guardrail_summary.csv
```

These are replay diagnostics, not a training corpus.

## Failure Taxonomy

Use:

```text
contour_aware_bounded_replay_public_pass:
  primary replay preserves clean contour and diagnostic controls remain negative.

primary_clean_shortfall:
  primary clean directed-pair count falls below 39.

source_share_failure:
  primary clean source-edge share exceeds 0.35.

diagnostic_control_failure:
  diagnostic rows no longer provide dominated/control evidence.

diagnostic_clean_leakage:
  diagnostic clean share exceeds 0.05.

variant_coverage_failure:
  one or more required intervention variants is missing.

anchor_replay_failure:
  too many target/donor anchor replays fail.

guardrail_violation:
  candidate materialization, corpus export, training, PPO, promotion, private
  holdout, actor-input change, or self-ID overclaim occurs.
```

## Route Decision

Admit one bounded implementation:

```text
m1605-paper-route-contour-aware-bounded-replay-implementation
```

If M1605 passes, route to audit before materialization or training. If it fails,
audit before patching. Do not directly continue into candidate export.

## Guardrails

```text
replay_started: false in M1604
history_interventions_executed: false in M1604
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
m1605-paper-route-contour-aware-bounded-replay-implementation
```
