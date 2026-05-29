# M1599 Paper-Route Clean Active-Set Contour Mapper Implementation

## Summary

M1599 implemented the offline clean active-set contour mapper designed by
M1598.

Decision:

```text
clean_active_set_contour_mapper_public_pass_route_to_audit
```

The mapper passed public smoke gates without replay, simulator rerun,
materialization, training, PPO, private holdout, actor-input change, or
threshold relaxation.

## Commands

Focused tests:

```bash
PYTHONPATH=src python -m pytest tests/test_clean_active_set_contour_mapper.py -q
```

Result:

```text
3 passed
```

Offline mapper:

```bash
PYTHONPATH=src python -m autodrift.clean_active_set_contour_mapper \
  --output-dir runs/m1599_clean_active_set_contour_mapper
```

Result:

```text
passes_public_smoke_gates: true
null_result_classification: contour_mapping_public_pass
```

## Artifacts

```text
runs/m1599_clean_active_set_contour_mapper/summary.json
runs/m1599_clean_active_set_contour_mapper/enriched_contour_rows.csv
runs/m1599_clean_active_set_contour_mapper/source_run_summary.csv
runs/m1599_clean_active_set_contour_mapper/source_edge_contour_summary.csv
runs/m1599_clean_active_set_contour_mapper/feature_group_summary.csv
runs/m1599_clean_active_set_contour_mapper/selection_source_summary.csv
runs/m1599_clean_active_set_contour_mapper/guardrail_summary.csv
```

## Result

```text
input_source_run_count: 3
input_directed_pair_count: 528
enriched_directed_pair_count: 528
metadata_joined_count: 528
metadata_joined_fraction: 1.0
clean_directed_pair_count: 51
dominated_history_positive_directed_pair_count: 72
control_only_positive_directed_pair_count: 79
history_null_all_controls_null_directed_pair_count: 326
invalid_directed_pair_count: 0
source_edge_count: 24
feature_group_count: 398
clean_source_edge_count: 5
max_clean_source_edge_share: 0.35294117647058826
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
null_result_classification: contour_mapping_public_pass
guardrail_violation_count: 0
```

## Source-Run Summary

```text
M1588 selector:
  directed pairs: 144
  clean: 7
  dominated: 16
  control-only: 28
  null: 93
  clean share: 0.0486

M1592 clean repair:
  directed pairs: 192
  clean: 34
  dominated: 39
  control-only: 18
  null: 101
  clean share: 0.1771

M1595 balanced repair:
  directed pairs: 192
  clean: 10
  dominated: 17
  control-only: 33
  null: 132
  clean share: 0.0521
```

M1592 is clearly the best contour so far.

## Selection-Source Contour

The strongest positive selection source is `clean_edge_window`:

```text
M1592 clean_edge_window:
  directed pairs: 112
  clean: 29
  clean share: 0.2589

M1595 clean_edge_window:
  directed pairs: 32
  clean: 10
  clean share: 0.3125
```

The over-balanced failure is explained by broad expansion:

```text
M1595 clean_endpoint_neighbor:
  directed pairs: 120
  clean: 0
  control-only: 19
  null: 101

M1595 negative_diagnostic_edge:
  directed pairs: 40
  clean: 0
  dominated: 13
  control-only: 13
  null: 14
```

This means the clean contour is not "all source-diverse pairable edges". It is
mostly source/window specific.

## Top Clean Source Edges

```text
actuator_delay_step|capability_step_up:
  clean: 18 / 48
  clean share: 0.375

curved_boundary_obstacle|t5_boundary_axis_retarget:
  clean: 14 / 48
  clean share: 0.2917

actuator_delay_step|t5_near_boundary_warmup:
  clean: 10 / 48
  clean share: 0.2083

capability_step_down|t5_near_boundary_warmup:
  clean: 7 / 48
  clean share: 0.1458

capability_step_up|t5_near_boundary_warmup:
  clean: 2 / 48
  dominated: 22 / 48
```

The last edge is mostly dominated despite having some clean rows. It should be a
diagnostic/contrast edge, not a primary expansion target.

## Interpretation

M1599 supports a clearer next hypothesis:

```text
clean active-set evidence is concentrated in source/window contours,
especially clean_edge_window rows on a small set of source edges.
```

M1599 also explains M1595:

```text
round-robin source balancing selected too many clean_endpoint_neighbor and
negative_diagnostic_edge rows, which are mostly null/dominated/control-only.
```

This does not admit materialization or training. It only provides a better
diagnostic basis for the next audit.

## Failure Taxonomy

```text
scenario_sampling_failure
objective_overfit
```

The mapper itself passed. The taxonomy describes the branch context: source
sampling is contour-sensitive, and local public-row cap tuning risks overfit.

## Guardrails

```text
replay_started: false
history_interventions_executed: false in M1599
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

Route to audit:

```text
m1600-paper-route-clean-contour-mapper-result-audit
```

The audit should decide whether to design a contour-aware source rule, stop the
branch, or pivot to task/source redesign. It must not route directly to replay
or training.
