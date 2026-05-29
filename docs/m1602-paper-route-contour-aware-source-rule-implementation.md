# M1602 Paper-Route Contour-Aware Source Rule Implementation

## Summary

M1602 implements the offline contour-aware source rule designed in M1601.

Decision:

```text
contour_aware_source_rule_public_pass_route_to_audit
```

The implementation is offline only. It reads M1599 enriched contour rows and
writes primary, diagnostic, excluded, summary, and guardrail artifacts. It does
not replay, rerun the simulator, materialize candidates, export a training
corpus, train, run PPO, promote, or use private holdout.

## Commands

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_contour_aware_source_rule.py -q
```

Result:

```text
3 passed in 0.89s
```

Offline source rule:

```text
PYTHONPATH=src python -m autodrift.contour_aware_source_rule --output-dir runs/m1602_contour_aware_source_rule
```

Result:

```text
passes_public_smoke_gates=True
null_result_classification=contour_aware_source_rule_public_pass
```

## Artifacts

```text
runs/m1602_contour_aware_source_rule/summary.json
runs/m1602_contour_aware_source_rule/primary_rule_rows.csv
runs/m1602_contour_aware_source_rule/diagnostic_rule_rows.csv
runs/m1602_contour_aware_source_rule/excluded_rule_rows.csv
runs/m1602_contour_aware_source_rule/source_rule_summary.csv
runs/m1602_contour_aware_source_rule/guardrail_summary.csv
```

## Gate Results

```text
input_contour_row_count: 528
primary_rule_directed_pair_count: 144
primary_source_edge_count: 4
primary_clean_directed_pair_count: 39
primary_clean_source_edge_count: 4
max_primary_clean_source_edge_share: 0.3333333333333333
endpoint_neighbor_primary_count: 0
negative_diagnostic_primary_count: 0
mixed_diagnostic_primary_count: 0
diagnostic_directed_pair_count: 232
diagnostic_dominated_or_control_count: 81
excluded_directed_pair_count: 152
guardrail_violation_count: 0
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
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
history_control_separated: 2
history_positive_control_dominated: 39
control_only_positive: 42
history_null_all_controls_null: 149
```

## Interpretation

The strict `clean_edge_window` primary rule preserves the desired contour:

```text
144 primary rows
39 clean rows
4 primary clean source edges
0 endpoint-neighbor leakage
0 negative-diagnostic leakage
0 mixed-edge leakage
```

The diagnostic set remains large enough to preserve the negative evidence:

```text
endpoint-neighbor diagnostics: 120 rows
negative-edge diagnostics: 64 rows
mixed-edge diagnostics: 48 rows
dominated/control diagnostic rows: 81
```

This supports the source-rule implementation, not replay or training. The next
step must audit whether this offline selector is strong enough to justify a
bounded replay design.

## Guardrails

```text
replay_started: false
history_interventions_executed: false
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
m1603-paper-route-contour-aware-source-rule-result-audit
```
