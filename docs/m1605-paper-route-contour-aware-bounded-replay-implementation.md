# M1605 Paper-Route Contour-Aware Bounded Replay Implementation

## Summary

M1605 implements the bounded replay designed by M1604.

Decision:

```text
contour_aware_bounded_replay_diagnostic_control_failure_route_to_audit
```

The final replay run preserves the primary clean contour, but the bounded
diagnostic sample does not preserve enough dominated/control evidence. This is
a public-gate failure and must route to audit before changing the diagnostic
sampling rule.

## Implementation Note

The first run exposed a metric artifact: `pair_id` values such as
`selected-0000|left_target` collide across source runs. The implementation was
fixed to use stable replay ids of the form:

```text
source_run::pair_id
```

The reported result below is from the corrected run.

## Commands

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_contour_aware_bounded_replay.py -q
```

Result:

```text
3 passed
```

Bounded replay:

```text
PYTHONPATH=src python -m autodrift.contour_aware_bounded_replay --output-dir runs/m1605_contour_aware_bounded_replay
```

Result:

```text
passes_public_smoke_gates=False
null_result_classification=diagnostic_control_failure
```

## Artifacts

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

## Gate Results

```text
primary_replay_directed_pair_count: 144
diagnostic_replay_directed_pair_count: 96
diagnostic_reason_count: 3
primary_source_run_count: 2
primary_source_edge_count: 4
primary_clean_directed_pair_count: 39
primary_clean_source_edge_count: 4
max_primary_clean_source_edge_share: 0.3333333333333333
endpoint_neighbor_primary_count: 0
negative_diagnostic_primary_count: 0
mixed_diagnostic_primary_count: 0
diagnostic_dominated_or_control_count: 35
diagnostic_clean_share: 0.0
required_variant_coverage_complete: true
anchor_replay_failure_count: 0
guardrail_violation_count: 0
passes_public_smoke_gates: false
```

Primary label counts:

```text
history_control_separated: 39
history_positive_control_dominated: 19
control_only_positive: 9
history_null_all_controls_null: 77
```

Diagnostic label counts:

```text
history_positive_control_dominated: 24
control_only_positive: 11
history_null_all_controls_null: 61
history_control_separated: 0
```

## Interpretation

The primary branch is good:

```text
clean count is preserved at 39;
source-edge share is preserved at 0.3333333333333333;
no endpoint-neighbor, negative-diagnostic, or mixed-diagnostic leakage entered primary;
all variants were covered;
anchor replay had zero failures.
```

The diagnostic branch failed its gate:

```text
diagnostic_dominated_or_control_count: 35
required: >= 50
```

The bounded diagnostic sample did not preserve enough negative/control evidence.
This is most likely a diagnostic sampling failure, not a primary contour failure.

## Guardrails

```text
replay_started: true
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

```text
m1606-paper-route-contour-aware-bounded-replay-result-audit
```
