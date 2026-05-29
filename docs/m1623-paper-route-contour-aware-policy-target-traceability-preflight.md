# M1623 Paper-Route Contour-Aware Policy Target Traceability Preflight

## Summary

M1623 implements and runs a source/variant traceability preflight before
policy-target materialization.

Decision:

```text
contour_aware_policy_target_traceability_preflight_public_pass_route_to_audit
```

This is infrastructure only. It does not materialize tensor targets, does not
construct a loss or objective config, does not update an actor, does not train,
does not run PPO, does not promote, and does not use private holdout.

## Implementation

New files:

```text
src/autodrift/contour_aware_policy_target_traceability_preflight.py
tests/test_contour_aware_policy_target_traceability_preflight.py
```

The preflight checks:

```text
M1615 positive candidate rows;
M1615 diagnostic guardrail rows;
M1609 replay_pair_rows.csv;
M1609 intervention_rows.csv;
source-run alias resolution for m1588_selector, m1592_clean_repair, m1595_balanced_repair;
normal / wrong_history_hidden / donor_response_action_plus_hidden variant availability.
```

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_contour_aware_policy_target_traceability_preflight.py
```

Result:

```text
2 passed in 2.10s
```

Run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.contour_aware_policy_target_traceability_preflight --candidate-run-dir runs/m1615_contour_aware_candidate_corpus --replay-run-dir runs/m1609_diagnostic_complete_bounded_replay --run-dir runs/m1623_contour_aware_policy_target_traceability_preflight
```

Result:

```text
passes_public_smoke_gates=True
null_result_classification=contour_aware_policy_target_traceability_preflight_public_pass
```

## Artifacts

```text
runs/m1623_contour_aware_policy_target_traceability_preflight/summary.json
runs/m1623_contour_aware_policy_target_traceability_preflight/positive_traceability_rows.csv
runs/m1623_contour_aware_policy_target_traceability_preflight/diagnostic_traceability_rows.csv
runs/m1623_contour_aware_policy_target_traceability_preflight/source_run_resolution_summary.csv
runs/m1623_contour_aware_policy_target_traceability_preflight/variant_availability_summary.csv
runs/m1623_contour_aware_policy_target_traceability_preflight/missing_traceability_rows.csv
runs/m1623_contour_aware_policy_target_traceability_preflight/guardrail_summary.csv
```

## Result

Summary:

```text
positive_candidate_count: 39
diagnostic_guardrail_count: 232
source_run_resolution_failure_count: 0
positive_replay_pair_match_count: 39
diagnostic_replay_pair_match_count: 232
positive_normal_variant_match_count: 39
positive_wrong_history_hidden_variant_match_count: 39
positive_donor_response_action_plus_hidden_variant_match_count: 39
diagnostic_normal_variant_match_count: 232
diagnostic_wrong_history_hidden_variant_match_count: 232
diagnostic_donor_response_action_plus_hidden_variant_match_count: 232
diagnostic_rows_used_as_positive: false
missing_traceability_row_count: 0
tensor_target_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

Source-run resolution:

```text
m1588_selector: 8 rows resolved
m1592_clean_repair: 93 rows resolved
m1595_balanced_repair: 170 rows resolved
```

Variant availability:

```text
positive_candidate:
  normal: 39 / 39
  wrong_history_hidden: 39 / 39
  donor_response_action_plus_hidden: 39 / 39

diagnostic_guardrail:
  normal: 232 / 232
  wrong_history_hidden: 232 / 232
  donor_response_action_plus_hidden: 232 / 232
```

## Interpretation

M1623 is a positive traceability preflight. It confirms the current package is
ready for a bounded tensor-capture materialization design or implementation
audit:

```text
all positive rows can be traced to M1609 replay pairs;
all diagnostic rows can be traced to M1609 replay pairs;
the key normal/wrong/donor-plus-hidden variants exist for every row;
source-run alias resolution is complete;
no tensor corpus or training artifact was written.
```

It still does not prove tensor capture itself works. The next audit must decide
whether to implement deterministic fixed-policy tensor capture or first add a
smaller capture dry-run.

## Unsupported Claims

M1623 does not support:

```text
tensor target materialization;
objective/loss construction;
actor update;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level validation;
closed-loop behavior improvement;
level3 anticipatory self-identification.
```

## Next

Route to result audit:

```text
m1624-paper-route-contour-aware-policy-target-traceability-result-audit
```
