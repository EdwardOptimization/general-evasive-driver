# M1587 Paper-Route History-vs-Control Active-Set Selector Design

## Summary

M1587 designs a selector-only diagnostic step after M1586.

Decision:

```text
history_vs_control_active_set_selector_design_admit_selector_only_implementation
```

The next implementation should not rerun the simulator and should not run more
history interventions. It should classify the existing M1585 directed pairs into
clean, dominated, and null active-set labels, then decide whether enough clean
surface exists for a future source-generation repair.

## Motivation

M1585 showed:

```text
history_positive_directed_pair_count: 23
clean history-vs-control directed pairs: 7
dominated history-positive directed pairs: 16
history-null directed pairs: 121
```

The broad pairability selector is too permissive. The next source-generation
objective must target history-vs-control separation directly.

## Inputs

Primary input:

```text
runs/m1585_source_diverse_pairability_history_intervention_smoke/intervention_rows.csv
```

Optional supporting inputs:

```text
runs/m1585_source_diverse_pairability_history_intervention_smoke/summary.json
runs/m1585_source_diverse_pairability_history_intervention_smoke/source_edge_summary.csv
runs/m1585_source_diverse_pairability_history_intervention_smoke/selected_pair_rows.csv
```

## Directed-Pair Aggregation

Group rows by:

```text
pair_id
```

For each directed pair compute:

```text
history_max_gap =
  max gap over wrong_history_hidden and donor_response_action_plus_hidden

wrong_history_gap =
  gap for wrong_history_hidden

donor_plus_hidden_gap =
  gap for donor_response_action_plus_hidden

donor_response_action_only_gap =
  gap for donor_response_action_only

control_max_gap =
  max gap over donor_response_action_only, reset_hidden,
  zero_current_response, zero_action_history, zero_all_response

hidden_specific_gap =
  donor_plus_hidden_gap - donor_response_action_only_gap

history_success_drop =
  any history variant causes success drop

control_success_drop =
  any control variant causes success drop
```

## Labels

Use these pre-registered labels.

```text
history_control_separated:
  history_max_gap >= 0.02
  and control_max_gap < 0.75 * history_max_gap
  and (
    hidden_specific_gap >= 0.01
    or wrong_history_gap >= 0.02
    or history_success_drop and not control_success_drop
  )

history_positive_control_dominated:
  history_max_gap >= 0.02 or history_success_drop
  but not history_control_separated

control_only_positive:
  history_max_gap < 0.02
  and not history_success_drop
  and (control_max_gap >= 0.02 or control_success_drop)

history_null_all_controls_null:
  history_max_gap < 0.02
  and control_max_gap < 0.02
  and no history/control success drop

replay_or_metric_invalid:
  normal row missing, nonfinite gap, or any required variant missing.
```

The first label is the only clean active-set candidate label.

## Public Gates For M1588

M1588 is selector-only and should pass public diagnostic gates if:

```text
input_directed_pair_count >= 144
required_variant_coverage_complete == true
classified_directed_pair_count >= 144
clean_directed_pair_count >= 7
clean_source_edge_count >= 4
dominated_history_positive_directed_pair_count >= 16
null_or_control_only_directed_pair_count >= 100
guardrail_violation_count == 0
history_interventions_executed == false
candidate_materialized == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
training_corpus_exported == false
```

Evidence-quality targets for the selector itself:

```text
clean_directed_pair_count >= 8
clean_source_edge_count >= 4
clean_endpoint_source_family_count >= 4
max_clean_source_edge_share <= 0.40
```

The expected current result is likely:

```text
clean_directed_pair_count: 7
```

Therefore M1588 may pass public diagnostic gates but fail evidence-quality
targets. That is acceptable as long as it routes to audit rather than relaxing
the threshold.

## Required Artifacts For M1588

```text
runs/m1588_history_vs_control_active_set_selector/classified_directed_pair_rows.csv
runs/m1588_history_vs_control_active_set_selector/clean_directed_pair_rows.csv
runs/m1588_history_vs_control_active_set_selector/source_edge_summary.csv
runs/m1588_history_vs_control_active_set_selector/source_family_summary.csv
runs/m1588_history_vs_control_active_set_selector/label_summary.csv
runs/m1588_history_vs_control_active_set_selector/guardrail_summary.csv
runs/m1588_history_vs_control_active_set_selector/summary.json
```

Do not export a training corpus. These are diagnostic rows.

## Null Classification

Use:

```text
selector_public_pass_clean_shortfall:
  public selector gates pass but clean count is below evidence-quality target.

source_singleton_clean_surface:
  clean count exists but source-edge share is too concentrated.

clean_surface_absent:
  clean count is zero.

metric_invalid:
  required variants are missing or nonfinite.

selector_public_and_evidence_pass:
  public and evidence-quality targets pass.
```

## Follow-Up Logic

If M1588 confirms `clean_directed_pair_count < 8`:

```text
audit first, then design source-generation repair using clean-label criteria.
```

If M1588 finds enough clean rows:

```text
audit first, then design a bounded clean-surface intervention repeat.
```

No materialization or training is admitted by M1587.

## Guardrails

```text
history_interventions_executed: false in M1587
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
m1588-paper-route-history-vs-control-active-set-selector-implementation
```
