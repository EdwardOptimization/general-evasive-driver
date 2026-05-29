# M1598 Paper-Route Clean Active-Set Contour Mapping Design

## Summary

M1598 designs the offline clean active-set contour mapper after the M1597 pivot.

Decision:

```text
clean_active_set_contour_mapping_design_admit_offline_implementation
```

The next step should not replay, train, materialize, or tune another cap. It
should first map the existing public active-set contour across M1588, M1592, and
M1595 to explain why M1592 was a near-pass and M1595 failed.

## Inputs

Use only existing public artifacts:

```text
runs/m1588_history_vs_control_active_set_selector/classified_directed_pair_rows.csv
runs/m1585_source_diverse_pairability_history_intervention_smoke/intervention_rows.csv

runs/m1592_clean_history_control_source_generation_repair_smoke/classified_directed_pair_rows.csv
runs/m1592_clean_history_control_source_generation_repair_smoke/intervention_rows.csv
runs/m1592_clean_history_control_source_generation_repair_smoke/selected_pair_rows.csv

runs/m1595_selector_balanced_clean_source_repair_smoke/classified_directed_pair_rows.csv
runs/m1595_selector_balanced_clean_source_repair_smoke/intervention_rows.csv
runs/m1595_selector_balanced_clean_source_repair_smoke/selected_pair_rows.csv
```

The mapper may join classified rows to intervention rows by `pair_id`, using the
`normal` variant as the metadata source. It must not rerun the simulator or
generate new intervention rows.

## Label Taxonomy

Preserve the existing selector labels:

```text
history_control_separated
history_positive_control_dominated
control_only_positive
history_null_all_controls_null
replay_or_metric_invalid
```

`history_control_separated` is the only clean label. Dominated and control-only
rows must remain diagnostics, not hidden successes.

## Contour Features

The offline mapper should produce one enriched row per directed pair with:

```text
source_run
pair_id
source_edge
target_source_family
donor_source_family
target_anchor_window
donor_anchor_window
same_window
step_distance
target_anchor_step
donor_anchor_step
direction
selection_source
original_pair_id
pair_response_action_l2
pair_context_l2
pair_hidden_l2
normal_terminal_margin
history_max_gap
control_max_gap
wrong_history_gap
donor_plus_hidden_gap
donor_response_action_only_gap
hidden_specific_gap
label
```

It should also derive coarse bands:

```text
history_gap_band
control_gap_band
hidden_specific_gap_band
response_action_l2_band
context_l2_band
hidden_l2_band
normal_margin_band
window_pair
family_pair
clean_positive
control_dominated_positive
control_only_positive
```

Banding is diagnostic only. It must not modify selector thresholds.

## Required Summaries

M1599 should write:

```text
runs/m1599_clean_active_set_contour_mapper/summary.json
runs/m1599_clean_active_set_contour_mapper/enriched_contour_rows.csv
runs/m1599_clean_active_set_contour_mapper/source_run_summary.csv
runs/m1599_clean_active_set_contour_mapper/source_edge_contour_summary.csv
runs/m1599_clean_active_set_contour_mapper/feature_group_summary.csv
runs/m1599_clean_active_set_contour_mapper/selection_source_summary.csv
runs/m1599_clean_active_set_contour_mapper/guardrail_summary.csv
```

The `feature_group_summary.csv` should group by combinations such as:

```text
source_run + source_edge
source_edge + target_anchor_window + donor_anchor_window
source_edge + selection_source
source_edge + history_gap_band + control_gap_band
source_edge + hidden_specific_gap_band
```

The implementation should keep this as an analysis artifact, not a training
dataset.

## Public Gates

M1599 should pass only if:

```text
input_source_run_count >= 3
input_directed_pair_count >= 528
enriched_directed_pair_count >= 528
metadata_joined_fraction >= 0.90
clean_directed_pair_count >= 51
dominated_history_positive_directed_pair_count >= 70
control_only_positive_directed_pair_count >= 79
history_null_all_controls_null_directed_pair_count >= 300
source_edge_count >= 20
feature_group_count >= 40
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

These gates test that the mapper covers the existing public contour. They do not
claim a driver result.

## Null Taxonomy

Use:

```text
contour_mapping_public_pass:
  artifacts are complete and coverage gates pass.

metadata_join_shortfall:
  classified rows cannot be joined to enough intervention metadata.

label_coverage_shortfall:
  one or more label families are missing or unexpectedly low.

feature_group_shortfall:
  grouping is too coarse to explain the contour.

guardrail_violation:
  replay/training/materialization/private holdout or actor-input changes occurred.
```

## Route Decision

Admit an offline implementation:

```text
m1599-paper-route-clean-active-set-contour-mapper-implementation
```

If M1599 passes, the next audit should decide whether the contour is clear
enough to design a new active-set source rule, or whether the branch should stop
or pivot to task/source redesign.

If M1599 fails, audit before changing the mapper. Do not immediately replay.

## Guardrails

```text
history_interventions_executed: false in M1598
replay_started: false
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
m1599-paper-route-clean-active-set-contour-mapper-implementation
```
