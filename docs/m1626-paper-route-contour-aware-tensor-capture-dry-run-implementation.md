# M1626 Paper-Route Contour-Aware Tensor Capture Dry-Run Implementation

## Summary

M1626 implements and runs the four-row deterministic tensor-capture dry run
designed in M1625.

Decision:

```text
contour_aware_tensor_capture_dry_run_public_pass_route_to_audit
```

This is infrastructure only. It captures a bounded dry-run tensor package for
four public rows, but it does not materialize the full target corpus, construct
a loss or objective config, update an actor, train, run PPO, promote a
checkpoint, use private holdout, change actor inputs, or claim level3
self-identification.

## Implementation

New files:

```text
src/autodrift/contour_aware_tensor_capture_dry_run.py
tests/test_contour_aware_tensor_capture_dry_run.py
```

The implementation reuses the existing fixed-policy replay path:

```text
M1609 replay_pair_rows.csv
-> pairability source specs and anchor candidates
-> replay_to_anchor
-> canonical P0 observation and online-GRU hidden capture
-> deterministic model.act_recurrent for normal / wrong-history / donor-plus-hidden actions
```

No tensor is fabricated from CSV-only metadata. The source CSV action rows are
used only as traceability checks, and the recomputed first actions match them.

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_contour_aware_tensor_capture_dry_run.py
```

Result:

```text
2 passed in 0.92s
```

Dry run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.contour_aware_tensor_capture_dry_run --candidate-run-dir runs/m1615_contour_aware_candidate_corpus --replay-run-dir runs/m1609_diagnostic_complete_bounded_replay --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt --run-dir runs/m1626_contour_aware_tensor_capture_dry_run
```

Result:

```text
passes_public_smoke_gates=True
null_result_classification=contour_aware_tensor_capture_dry_run_public_pass
```

## Artifacts

```text
runs/m1626_contour_aware_tensor_capture_dry_run/summary.json
runs/m1626_contour_aware_tensor_capture_dry_run/captured_target_rows.csv
runs/m1626_contour_aware_tensor_capture_dry_run/captured_targets.npz
runs/m1626_contour_aware_tensor_capture_dry_run/capture_traceability_rows.csv
runs/m1626_contour_aware_tensor_capture_dry_run/shape_summary.csv
runs/m1626_contour_aware_tensor_capture_dry_run/guardrail_summary.csv
runs/m1626_contour_aware_tensor_capture_dry_run/missing_capture_rows.csv
```

## Result

Summary:

```text
dry_run_row_count: 4
positive_capture_count: 2
diagnostic_capture_count: 2
normal_variant_match_count: 4
wrong_history_variant_match_count: 4
donor_plus_hidden_variant_match_count: 4
missing_capture_row_count: 0
observation_shape: [4, 72]
preferred_action_shape: [4, 3]
wrong_history_action_shape: [4, 3]
donor_plus_hidden_action_shape: [4, 3]
hidden_dim: 128
correct_hidden_shape_ok: true
wrong_hidden_shape_ok: true
all_tensor_values_finite: true
diagnostic_rows_used_as_positive: false
checkpoint_weights_mutated: false
guardrail_violation_count: 0
```

Captured arrays:

```text
observation: float32 4x72 finite
correct_hidden: float32 4x128 finite
wrong_hidden: float32 4x128 finite
preferred_action: float32 4x3 finite
wrong_history_action: float32 4x3 finite
donor_plus_hidden_action: float32 4x3 finite
```

Traceability:

```text
source_preferred_action_l2: 0.0 for all four rows
source_wrong_history_action_l2: 0.0 for all four rows
source_donor_plus_hidden_action_l2: 0.0 for all four rows
```

Diagnostics remain guardrails:

```text
m1588_selector::selected-0020|left_target: used_as_positive=false, role_weight=0.0
m1595_balanced_repair::selected-0004|left_target: used_as_positive=false, role_weight=0.0
```

## Interpretation

M1626 proves that the current M1615/M1609 public rows can be rerun into
policy-side tensors for a small source-diverse subset:

```text
canonical actor observation is available;
correct and wrong online-GRU hidden states are available;
normal / wrong-history / donor-plus-hidden first actions are deterministic;
the capture path reproduces existing M1609 action metadata exactly;
diagnostics can be carried without becoming positive targets.
```

This removes the immediate tensor-capture plumbing blocker for the dry-run
subset. It does not yet prove that full target materialization is safe.

## Unsupported Claims

M1626 does not support:

```text
full target corpus materialization;
objective/loss construction;
actor update;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level validation;
level3 anticipatory self-identification.
```

## Next

Route to result audit before full materialization:

```text
m1627-paper-route-contour-aware-tensor-capture-dry-run-result-audit
```
