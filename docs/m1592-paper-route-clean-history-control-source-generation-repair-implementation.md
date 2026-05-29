# M1592 Paper-Route Clean History-Control Source-Generation Repair Implementation

## Summary

M1592 implemented and ran the bounded clean history-vs-control source-generation
repair admitted by M1591.

Decision:

```text
clean_history_control_source_generation_repair_near_pass_source_concentration_route_to_audit
```

The implementation is a strong diagnostic improvement but not a public gate
pass. It increased the clean surface from M1588's 7 clean directed pairs to 34
clean directed pairs and from 4 clean source edges to 5 clean source edges, with
zero invalid directed pairs. The pre-registered max clean source-edge share gate
failed narrowly:

```text
max_clean_source_edge_share: 0.35294117647058826
gate: <= 0.35
```

No threshold was relaxed and no second repair was run. The result routes to
audit.

## Commands

Focused tests:

```bash
PYTHONPATH=src python -m pytest tests/test_clean_history_control_source_generation_repair.py -q
```

Result:

```text
3 passed
```

Smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.clean_history_control_source_generation_repair \
  --output-dir runs/m1592_clean_history_control_source_generation_repair_smoke \
  --seed 1901 \
  --max-source-specs 480 \
  --max-selected-pairs 96 \
  --device cpu
```

The seed is `1901` because the input M1582 pairability rows were generated from
that source-spec set. A pre-result configuration mistake using a different seed
created missing-anchor invalid rows; it was corrected before recording the
M1592 result.

## Artifacts

```text
runs/m1592_clean_history_control_source_generation_repair_smoke/summary.json
runs/m1592_clean_history_control_source_generation_repair_smoke/source_spec_rows.csv
runs/m1592_clean_history_control_source_generation_repair_smoke/selected_pair_rows.csv
runs/m1592_clean_history_control_source_generation_repair_smoke/intervention_rows.csv
runs/m1592_clean_history_control_source_generation_repair_smoke/classified_directed_pair_rows.csv
runs/m1592_clean_history_control_source_generation_repair_smoke/clean_directed_pair_rows.csv
runs/m1592_clean_history_control_source_generation_repair_smoke/source_edge_summary.csv
runs/m1592_clean_history_control_source_generation_repair_smoke/label_summary.csv
runs/m1592_clean_history_control_source_generation_repair_smoke/variant_summary.csv
runs/m1592_clean_history_control_source_generation_repair_smoke/guardrail_summary.csv
```

## Result

```text
source_spec_count: 480
selected_pair_count: 96
selected_source_edge_count: 7
selected_endpoint_source_family_count: 6
selected_window_count: 6
directed_pair_count: 192
intervention_row_count: 1536
classified_directed_pair_count: 192
required_variant_coverage_complete: true
invalid_directed_pair_count: 0
clean_directed_pair_count: 34
clean_source_edge_count: 5
clean_endpoint_source_family_count: 6
max_clean_source_edge_share: 0.35294117647058826
dominated_history_positive_directed_pair_count: 39
control_only_positive_directed_pair_count: 18
history_null_all_controls_null_directed_pair_count: 101
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
null_result_classification: source_concentrated_clean_surface
guardrail_violation_count: 0
```

Label counts:

```text
history_control_separated: 34
history_positive_control_dominated: 39
control_only_positive: 18
history_null_all_controls_null: 101
```

## Source-Edge Breakdown

```text
actuator_delay_step|capability_step_up:
  directed pairs 32
  clean 12
  dominated 2
  null 18

actuator_delay_step|t5_near_boundary_warmup:
  directed pairs 32
  clean 6
  null 26

capability_step_down|t5_near_boundary_warmup:
  directed pairs 32
  clean 5
  dominated 11
  control-only 5
  null 11

capability_step_up|t5_near_boundary_warmup:
  directed pairs 32
  clean 2
  dominated 14
  control-only 2
  null 14

curved_boundary_obstacle|t5_boundary_axis_retarget:
  directed pairs 32
  clean 9
  dominated 4
  control-only 3
  null 16

capability_step_up|curved_boundary_obstacle:
  directed pairs 4
  clean 0
  dominated 2
  null 2

capability_step_up|t5_boundary_axis_retarget:
  directed pairs 28
  clean 0
  dominated 6
  control-only 8
  null 14
```

## Interpretation

M1592 supports that the clean-source repair objective is useful:

```text
M1588 clean directed pairs: 7
M1592 clean directed pairs: 34

M1588 clean source edges: 4
M1592 clean source edges: 5

M1592 invalid directed pairs: 0
```

It does not support promotion or materialization because the strict source-share
gate failed. The failure is narrow but real. The largest clean edge,
`actuator_delay_step|capability_step_up`, contributes 12 of 34 clean rows,
slightly exceeding the pre-registered share cap.

The large dominated and control-only counts remain useful. They show that the
selector is still protecting the research question from current-frame/action
history substitution.

## Failure Taxonomy

```text
scenario_sampling_failure
```

The repair found enough clean rows and enough clean source edges, but the
sampled clean surface remains slightly too concentrated.

## Guardrails

```text
history_interventions_executed: true
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

Route to result audit:

```text
m1593-paper-route-clean-source-repair-result-audit
```

The audit should decide whether the near-pass justifies a selector-balanced cap
repair design, whether to stop the branch, or whether to pivot to task/source
redesign. It must not treat the narrow source-share miss as a pass by
post-hoc threshold relaxation.
