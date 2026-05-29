# M1630 Paper-Route Contour-Aware Full Target Materialization Implementation

## Summary

M1630 implements and runs the full contour-aware policy-target materialization
specified in M1629.

Decision:

```text
contour_aware_full_target_materialization_public_pass_route_to_audit
```

This is infrastructure only. It materializes policy-side tensor bundles for the
public 39 positive rows and 232 diagnostic guardrail rows. It does not construct
a loss or objective config, update an actor, train, run PPO, promote a
checkpoint, use private holdout, change actor inputs, or claim level3
self-identification.

## Implementation

New files:

```text
src/autodrift/contour_aware_full_target_materialization.py
tests/test_contour_aware_full_target_materialization.py
```

The implementation reuses the M1626 capture primitives:

```text
M1615 candidate package
-> M1609 replay/intervention package
-> fixed-policy anchor replay
-> canonical P0 observation and online-GRU hidden capture
-> deterministic normal / wrong-history / donor-plus-hidden action capture
-> split positive-target and diagnostic-guardrail tensor bundles
```

Diagnostics are carried as guardrails:

```text
used_as_positive=false
role_weight=0.0
training_ready=false
```

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_contour_aware_full_target_materialization.py
```

Result:

```text
2 passed in 2.09s
```

Full materialization:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.contour_aware_full_target_materialization --candidate-run-dir runs/m1615_contour_aware_candidate_corpus --replay-run-dir runs/m1609_diagnostic_complete_bounded_replay --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt --run-dir runs/m1630_contour_aware_full_target_materialization
```

Result:

```text
positive_policy_target_count=39
diagnostic_policy_guardrail_count=232
hidden_dim=128
passes_public_smoke_gates=True
null_result_classification=contour_aware_full_target_materialization_public_pass
```

## Artifacts

```text
runs/m1630_contour_aware_full_target_materialization/summary.json
runs/m1630_contour_aware_full_target_materialization/positive_policy_target_rows.csv
runs/m1630_contour_aware_full_target_materialization/diagnostic_policy_guardrail_rows.csv
runs/m1630_contour_aware_full_target_materialization/positive_policy_targets.npz
runs/m1630_contour_aware_full_target_materialization/diagnostic_policy_guardrails.npz
runs/m1630_contour_aware_full_target_materialization/capture_traceability_rows.csv
runs/m1630_contour_aware_full_target_materialization/shape_summary.csv
runs/m1630_contour_aware_full_target_materialization/source_summary.csv
runs/m1630_contour_aware_full_target_materialization/guardrail_summary.csv
runs/m1630_contour_aware_full_target_materialization/missing_capture_rows.csv
```

## Result

Summary:

```text
positive_input_row_count: 39
diagnostic_input_row_count: 232
positive_policy_target_count: 39
diagnostic_policy_guardrail_count: 232
missing_capture_row_count: 0
hidden_dim: 128
positive_all_tensor_values_finite: true
diagnostic_all_tensor_values_finite: true
diagnostic_rows_used_as_positive: false
diagnostic_positive_weight_sum: 0.0
positive_source_action_l2_max: 0.0
diagnostic_source_action_l2_max: 0.0
checkpoint_weights_mutated: false
guardrail_violation_count: 0
```

Positive tensors:

```text
observation: float32 39x72 finite
correct_hidden: float32 39x128 finite
wrong_hidden: float32 39x128 finite
preferred_action: float32 39x3 finite
wrong_history_action: float32 39x3 finite
donor_plus_hidden_action: float32 39x3 finite
```

Diagnostic guardrail tensors:

```text
observation: float32 232x72 finite
correct_hidden: float32 232x128 finite
wrong_hidden: float32 232x128 finite
preferred_action: float32 232x3 finite
wrong_history_action: float32 232x3 finite
donor_plus_hidden_action: float32 232x3 finite
```

Source coverage:

```text
positive m1592_clean_repair: 29
positive m1595_balanced_repair: 10
diagnostic m1588_selector: 8
diagnostic m1592_clean_repair: 64
diagnostic m1595_balanced_repair: 160
```

## Interpretation

M1630 removes the immediate policy-side tensor materialization blocker. The
public contour-aware package now has separate positive-target and
diagnostic-guardrail tensor bundles with canonical 72-dim observations,
correct/wrong GRU hidden states, deterministic action targets, finite-value
guards, exact source-action reproduction, and role-integrity metadata.

This makes a later objective-design audit possible. It does not itself define a
loss, train a model, or prove that the policy uses history causally.

## Validation

```text
make research-validate: passed
python -m compileall -q src tests: passed
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q:
  1608 passed, 4 warnings in 8.56s
make check-diff: passed
```

## Unsupported Claims

M1630 does not support:

```text
objective/loss construction;
training corpus export;
actor update;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level validation;
level3 anticipatory self-identification.
```

## Next

Route to result audit before any objective design:

```text
m1631-paper-route-contour-aware-full-target-materialization-result-audit
```
