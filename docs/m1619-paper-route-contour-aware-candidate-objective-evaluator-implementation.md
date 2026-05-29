# M1619 Paper-Route Contour-Aware Candidate Objective Evaluator Implementation

## Summary

M1619 implements and runs a no-update exact evaluator over the M1615
contour-aware candidate package.

Decision:

```text
contour_aware_candidate_objective_evaluator_public_pass_route_to_audit
```

The evaluator is infrastructure only. It does not construct a loss config, does
not construct an objective config, does not update an actor, does not train,
does not run PPO, does not write a checkpoint, does not promote, and does not
use private holdout.

## Implementation

New files:

```text
src/autodrift/contour_aware_candidate_objective_evaluator.py
tests/test_contour_aware_candidate_objective_evaluator.py
```

The evaluator reads the audited M1615 package:

```text
runs/m1615_contour_aware_candidate_corpus/summary.json
runs/m1615_contour_aware_candidate_corpus/corpus_manifest.json
runs/m1615_contour_aware_candidate_corpus/positive_candidate_rows.csv
runs/m1615_contour_aware_candidate_corpus/diagnostic_guardrail_rows.csv
```

It writes:

```text
runs/m1619_contour_aware_candidate_objective_evaluator/summary.json
runs/m1619_contour_aware_candidate_objective_evaluator/positive_objective_rows.csv
runs/m1619_contour_aware_candidate_objective_evaluator/diagnostic_guardrail_objective_rows.csv
runs/m1619_contour_aware_candidate_objective_evaluator/role_integrity_summary.csv
runs/m1619_contour_aware_candidate_objective_evaluator/objective_summary.csv
runs/m1619_contour_aware_candidate_objective_evaluator/source_edge_summary.csv
runs/m1619_contour_aware_candidate_objective_evaluator/guardrail_summary.csv
```

The row-level residual is intentionally metadata/row-metric based. It uses the
available package metrics instead of fabricating policy log-probability targets:

```text
non_history_gap_max = max(control_max_gap, donor_response_action_only_gap)
history_control_separation_margin = history_max_gap - non_history_gap_max
candidate_objective_residual =
  softplus(non_history_gap_max - history_max_gap)
```

Diagnostics are written only as guardrail rows with:

```text
diagnostic_positive_weight: 0.0
used_as_positive: false
```

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_contour_aware_candidate_objective_evaluator.py
```

Result:

```text
3 passed in 2.11s
```

Run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.contour_aware_candidate_objective_evaluator --candidate-run-dir runs/m1615_contour_aware_candidate_corpus --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt --run-dir runs/m1619_contour_aware_candidate_objective_evaluator
```

Result:

```text
passes_public_smoke_gates=True
null_result_classification=contour_aware_candidate_objective_evaluator_public_pass
```

## Result

Summary:

```text
exact_evaluator_implemented: true
candidate_objective_evaluated: true
positive_candidate_count: 39
diagnostic_guardrail_count: 232
diagnostic_rows_used_as_positive: false
diagnostic_positive_weight_sum: 0.0
positive_rows_all_clean: true
role_metadata_verified: true
public_proof_metadata_complete: true
all_objective_metrics_finite: true
checkpoint_weights_mutated: false
guardrail_violation_count: 0
passes_public_smoke_gates: true
```

Objective metrics:

```text
candidate_objective_residual_mean: 0.6822030978276948
history_control_separation_margin_mean: 0.022017600571959638
hidden_specific_gap_mean: 0.021311087773094452
positive_finite_fraction: 1.0
diagnostic_finite_fraction: 1.0
```

Checkpoint mutation guard:

```text
checkpoint_sha256_before: fca7dded51cc9137a38511926700eeb215363bdb54991c727d6c4bb7620fd729
checkpoint_sha256_after:  fca7dded51cc9137a38511926700eeb215363bdb54991c727d6c4bb7620fd729
checkpoint_weights_mutated: false
```

## Interpretation

M1619 is a qualified infrastructure positive:

```text
the no-update evaluator exists;
the full M1615 package can be evaluated with finite row-metric residuals;
positive and diagnostic roles remain separated;
diagnostics cannot improve the positive objective;
checkpoint mutation protection is working.
```

It is not training evidence. The current package does not include action
sequence tensors or policy log-probability targets, so this evaluator correctly
stays at the package-metric residual layer. A future policy-side objective
would require a separate design that materializes action/hidden/observation
targets or explicitly declares the residual as metadata-only.

## Unsupported Claims

M1619 does not support:

```text
objective-only update;
actor update;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level validation;
closed-loop behavior improvement;
level3 anticipatory self-identification.
```

## Next

Route to result audit before any objective update:

```text
m1620-paper-route-contour-aware-candidate-objective-evaluator-result-audit
```
