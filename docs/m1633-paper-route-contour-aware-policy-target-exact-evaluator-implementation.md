# M1633 Paper-Route Contour-Aware Policy Target Exact Evaluator Implementation

## Summary

M1633 implements and runs the no-update exact evaluator admitted by M1632.

Decision:

```text
contour_aware_policy_target_exact_evaluator_public_pass_route_to_audit
```

This is infrastructure only. It evaluates the M1632 role-safe objective
semantics over the M1630 materialized tensors, but it does not write an
objective config artifact, update an actor, train, run PPO, promote a
checkpoint, use private holdout, change actor inputs, or claim level3
self-identification.

## Implementation

New files:

```text
src/autodrift/contour_aware_policy_target_exact_evaluator.py
tests/test_contour_aware_policy_target_exact_evaluator.py
```

The evaluator loads:

```text
runs/m1630_contour_aware_full_target_materialization/positive_policy_targets.npz
runs/m1630_contour_aware_full_target_materialization/diagnostic_policy_guardrails.npz
runs/m1630_contour_aware_full_target_materialization/positive_policy_target_rows.csv
runs/m1630_contour_aware_full_target_materialization/diagnostic_policy_guardrail_rows.csv
```

It recomputes deterministic actions under:

```text
pi(observation, correct_hidden)
pi(observation, wrong_hidden)
```

and reports action residuals plus separation metrics. It explicitly keeps
`donor_plus_hidden_action` as a diagnostic action only because the corresponding
donor-response observation was not materialized in M1630.

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_contour_aware_policy_target_exact_evaluator.py
```

Result:

```text
2 passed in 2.08s
```

Exact evaluator:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.contour_aware_policy_target_exact_evaluator --materialization-run-dir runs/m1630_contour_aware_full_target_materialization --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt --run-dir runs/m1633_contour_aware_policy_target_exact_evaluator
```

Result:

```text
positive_policy_target_count=39
diagnostic_policy_guardrail_count=232
positive_policy_action_residual_l2_max=0.0
diagnostic_policy_action_residual_l2_max=0.0
passes_public_smoke_gates=True
null_result_classification=contour_aware_policy_target_exact_evaluator_public_pass
```

## Artifacts

```text
runs/m1633_contour_aware_policy_target_exact_evaluator/summary.json
runs/m1633_contour_aware_policy_target_exact_evaluator/positive_objective_rows.csv
runs/m1633_contour_aware_policy_target_exact_evaluator/diagnostic_guardrail_rows.csv
runs/m1633_contour_aware_policy_target_exact_evaluator/objective_summary.csv
runs/m1633_contour_aware_policy_target_exact_evaluator/shape_summary.csv
runs/m1633_contour_aware_policy_target_exact_evaluator/guardrail_summary.csv
```

## Result

Summary:

```text
positive_policy_target_count: 39
diagnostic_policy_guardrail_count: 232
positive_observation_shape: [39, 72]
diagnostic_observation_shape: [232, 72]
positive_action_residuals_finite: true
diagnostic_action_residuals_finite: true
positive_policy_action_residual_l2_max: 0.0
diagnostic_policy_action_residual_l2_max: 0.0
positive_source_action_reproduction_l2_max: 0.0
diagnostic_source_action_reproduction_l2_max: 0.0
positive_exact_residual_mean: 0.0
diagnostic_exact_residual_mean: 1.808948061705878e-06
separation_margin: 0.05
donor_plus_action_used_as_loss_target: false
diagnostic_rows_used_as_positive: false
diagnostic_positive_weight_sum: 0.0
checkpoint_weights_mutated: false
```

Objective summary:

```text
positive target_sep_l2_min: 0.09100589626567962
positive target_sep_l2_mean: 0.2690623823631232
positive policy_sep_l2_mean: 0.2690623823631232
positive sep_residual_max: 0.0

diagnostic target_sep_l2_min: 0.029132609425989595
diagnostic target_sep_l2_mean: 0.24072096789296604
diagnostic policy_sep_l2_mean: 0.24072096789296604
diagnostic sep_residual_max: 0.020867390574010408
```

The positive exact residual is zero because M1630 captured the same checkpoint's
deterministic actions and M1633 re-evaluates the same policy. Diagnostic
separation residual is reported but remains zero-weight and non-positive.

## Interpretation

M1633 proves the no-update evaluator plumbing is valid for the materialized
public tensors. It can reproduce the base policy's correct/wrong hidden actions
exactly, verify diagnostic role integrity, and write exact objective metrics
without mutating the checkpoint.

This does not prove that an actor update is safe. The next step must audit the
evaluator result before deciding whether an objective-only update design is
admitted.

## Validation

```text
make research-validate: passed
python -m compileall -q src tests: passed
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q:
  1610 passed, 4 warnings in 7.44s
```

## Unsupported Claims

M1633 does not support:

```text
objective config artifact construction;
actor update;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
closed-loop behavior improvement;
paper-level validation;
level3 anticipatory self-identification.
```

## Next

Route to result audit before any actor update design:

```text
m1634-paper-route-contour-aware-policy-target-exact-evaluator-result-audit
```
