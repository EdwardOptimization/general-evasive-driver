# M1609 Paper-Route Diagnostic-Complete Bounded Replay Implementation

## Summary

M1609 runs the diagnostic-complete bounded replay admitted by M1608.

Decision:

```text
diagnostic_complete_bounded_replay_public_pass_route_to_audit
```

The result passes the pre-registered public smoke gates. It preserves the
primary clean contour and, unlike M1605's capped diagnostic sample, preserves
enough negative/control diagnostic evidence. This is still a public proof
diagnostic only. Candidate materialization, corpus export, training, PPO,
promotion, private holdout, actor-input changes, threshold relaxation, and
level3 self-ID claims remain blocked until result audit.

## Commands

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_contour_aware_bounded_replay.py -q
```

Result:

```text
3 passed in 2.08s
```

Replay:

```text
PYTHONPATH=src python -m autodrift.contour_aware_bounded_replay --output-dir runs/m1609_diagnostic_complete_bounded_replay --diagnostic-per-reason-cap 999
```

## Result

```text
primary_replay_directed_pair_count: 144
diagnostic_replay_directed_pair_count: 232
classified_directed_pair_count: 376
intervention_row_count: 3008
variant_count: 8
continuation_steps: 64
```

Primary replay:

```text
primary_source_run_count: 2
primary_source_edge_count: 4
primary_clean_directed_pair_count: 39
primary_clean_source_edge_count: 4
max_primary_clean_source_edge_share: 0.3333333333333333
endpoint_neighbor_primary_count: 0
negative_diagnostic_primary_count: 0
mixed_diagnostic_primary_count: 0
```

Diagnostic replay:

```text
diagnostic_reason_count: 3
diagnostic_clean_directed_pair_count: 2
diagnostic_clean_share: 0.008620689655172414
diagnostic_dominated_or_control_count: 81
```

Replay health:

```text
anchor_replay_failure_count: 0
invalid_directed_pair_count: 0
required_variant_coverage_complete: true
guardrail_violation_count: 0
passes_evidence_quality_targets: true
passes_public_smoke_gates: true
null_result_classification: contour_aware_bounded_replay_public_pass
```

## Labels

Primary label counts:

```text
history_control_separated: 39
history_positive_control_dominated: 19
control_only_positive: 9
history_null_all_controls_null: 77
```

Diagnostic label counts:

```text
history_control_separated: 2
history_positive_control_dominated: 39
control_only_positive: 42
history_null_all_controls_null: 149
```

Diagnostic reason summary:

```text
endpoint_neighbor_exclusion: 120 rows, 0 clean, 19 control-only, 101 null
mixed_dominated_edge: 48 rows, 2 clean, 22 dominated, 2 control-only, 22 null
negative_diagnostic_edge: 64 rows, 0 clean, 17 dominated, 21 control-only, 26 null
```

## Interpretation

M1609 answers the immediate M1605/M1607 question: the capped diagnostic sample
was too weak. Replaying all diagnostics label-blind preserves primary clean
contour evidence and gives enough dominated/control diagnostics to keep the
selector honest.

This does not prove broad generalization or level3 anticipatory
self-identification. It only says the contour-aware replay harness can preserve
both the primary clean surface and the diagnostic/control surface on the public
M1602 rows.

## Guardrails

```text
replay_started: true
history_interventions_executed: true
candidate_materialized: false
training_started: false
evaluation_started: false
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
m1610-paper-route-diagnostic-complete-bounded-replay-result-audit
```
