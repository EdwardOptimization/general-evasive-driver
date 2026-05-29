# M1612 Paper-Route Contour-Aware Candidate Materialization Implementation

## Summary

M1612 implements the offline materializer designed in M1611.

Decision:

```text
contour_aware_candidate_materialization_public_pass_route_to_audit
```

The implementation writes candidate-row artifacts and diagnostic guardrails
only. It does not export a training corpus, train, run PPO, promote, use private
holdout, change actor inputs, or claim level3 self-identification.

## Commands

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_contour_aware_candidate_materialization.py -q
```

Result:

```text
3 passed in 2.05s
```

Materializer:

```text
PYTHONPATH=src python -m autodrift.contour_aware_candidate_materialization --output-dir runs/m1612_contour_aware_candidate_materialization
```

## Result

```text
primary_input_directed_pair_count: 144
diagnostic_input_directed_pair_count: 232
candidate_directed_pair_count: 39
candidate_source_edge_count: 4
max_candidate_source_edge_share: 0.3333333333333333
candidate_rows_from_primary_only: true
candidate_rows_all_clean: true
candidate_rows_missing_variants_count: 0
candidate_pair_ids_unique: true
```

Diagnostic guardrails:

```text
diagnostic_guardrail_directed_pair_count: 232
diagnostic_reason_count: 3
diagnostic_dominated_or_control_count: 81
diagnostic_clean_share: 0.008620689655172414
diagnostic_rows_enter_candidate_rows: false
```

Guardrails:

```text
candidate_materialized: true
candidate_materialization_only: true
training_corpus_exported: false
training_started: false
evaluation_started: false
replay_started: false
history_interventions_executed: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
guardrail_violation_count: 0
```

Outcome:

```text
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
null_result_classification: contour_aware_candidate_materialization_public_pass
```

## Candidate Source Edges

```text
actuator_delay_step|capability_step_up: 13
actuator_delay_step|t5_near_boundary_warmup: 8
capability_step_down|t5_near_boundary_warmup: 6
curved_boundary_obstacle|t5_boundary_axis_retarget: 12
```

## Diagnostic Guardrail Reasons

```text
endpoint_neighbor_exclusion: 120 rows, 0 clean, 19 control-only, 101 null
mixed_dominated_edge: 48 rows, 2 clean, 22 dominated, 2 control-only, 22 null
negative_diagnostic_edge: 64 rows, 0 clean, 17 dominated, 21 control-only, 26 null
```

## Interpretation

M1612 successfully materializes the public-pass candidate surface as artifacts,
not as a training corpus. The materialized candidate set is narrow and public:
39 rows across four source edges. The diagnostic guardrail set remains separate
and should be audited before any training-corpus design.

## Artifacts

```text
runs/m1612_contour_aware_candidate_materialization/summary.json
runs/m1612_contour_aware_candidate_materialization/candidate_rows.csv
runs/m1612_contour_aware_candidate_materialization/candidate_source_edge_summary.csv
runs/m1612_contour_aware_candidate_materialization/diagnostic_guardrail_rows.csv
runs/m1612_contour_aware_candidate_materialization/diagnostic_guardrail_summary.csv
runs/m1612_contour_aware_candidate_materialization/guardrail_summary.csv
```

## Next

Route to result audit:

```text
m1613-paper-route-contour-aware-candidate-materialization-result-audit
```
