# M1640 Paper-Route Contour-Aware Exact Objective Projection Repair Implementation

## Summary

M1640 implemented the bounded no-checkpoint projection repair probe admitted by
M1639.

Decision:

```text
contour_aware_projection_repair_negative_route_to_result_audit
```

The implementation and focused tests passed, but the pre-registered projection
run did not reduce the positive exact residual. This is a negative result for
the specific M1638/M1640 optimizer recipe, not a failure of the tensor
materialization or exact evaluator plumbing.

No checkpoint was written, no PPO was run, no closed-loop training was started,
no private holdout was used, no actor inputs changed, diagnostics remained
zero-weight, donor-plus actions stayed excluded from loss targets, and no
level3 self-identification claim is made.

## Implementation

Added:

```text
src/autodrift/contour_aware_exact_objective_projection_repair.py
tests/test_contour_aware_exact_objective_projection_repair.py
```

The probe:

```text
base checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt

materialization:
  runs/m1630_contour_aware_full_target_materialization

input candidate:
  M1636 scale_1e-3 actor_mean perturbation
  perturb_seed: 1639

repair scope:
  actor_mean.weight
  actor_mean.bias

frozen:
  response/context encoders, GRU, fusion, critic, log_std, auxiliary heads

output:
  metrics only
  no .pt checkpoint
```

The differentiable loss matched the M1638 design:

```text
correct hidden -> preferred_action
wrong hidden   -> wrong_history_action
plus 0.25 * separation-collapse residual
```

Diagnostics were evaluated before and after repair but carried zero gradient
and zero positive weight.

## Validation

Focused test:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q tests/test_contour_aware_exact_objective_projection_repair.py
```

Result:

```text
2 passed in 3.12s
```

Official M1640 run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.contour_aware_exact_objective_projection_repair \
  --materialization-run-dir runs/m1630_contour_aware_full_target_materialization \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --run-dir runs/m1640_contour_aware_exact_objective_projection_repair
```

Artifacts:

```text
runs/m1640_contour_aware_exact_objective_projection_repair/summary.json
runs/m1640_contour_aware_exact_objective_projection_repair/repair_summary.csv
runs/m1640_contour_aware_exact_objective_projection_repair/guardrail_summary.csv
runs/m1640_contour_aware_exact_objective_projection_repair/optimization_trace.csv
```

## Result

Key metrics:

```text
initial_positive_exact_residual_mean:  0.0003143580979667604
repaired_positive_exact_residual_mean: 0.0003143580979667604
positive_exact_residual_reduction:     0.0
positive_exact_residual_reduction_ratio: 0.0

initial_positive_action_l2_max:  0.015652701258659363
repaired_positive_action_l2_max: 0.015652701258659363

initial_actor_mean_l2_to_base:  0.019672319293022156
repaired_actor_mean_l2_to_base: 0.019672319293022156

non_actor_mean_parameter_delta_max: 0.0
repaired_checkpoint_written: false
guardrail_violation_count: 0
passes_public_smoke_gates: false
null_result_classification: projection_residual_not_reduced
```

The initial perturbation was measurable and matched M1636 scale:

```text
initial_positive_exact_residual_mean > 1e-8
```

The repair did not improve it.

## Trace Interpretation

The run did not fail because gradients were disconnected:

```text
grad_norm_max: 4.537821292877197
```

The optimization trace shows that the first Adam step at `learning_rate=1e-3`
was too large relative to the `scale_1e-3` actor_mean perturbation:

```text
step 0 positive_exact_residual_mean: 0.0003143580979667604
step 1 positive_exact_residual_mean: 0.03115139901638031
step 1 actor_mean_l2_to_base:        0.026685267686843872
```

Later steps remained worse than the initial perturbed candidate, so the
trust-region best candidate stayed at step 0:

```text
best repaired residual == initial residual
```

This classifies the pre-registered projection recipe as optimizer-step
unstable for this small perturbation. It does not invalidate the M1630 tensor
materialization, the M1633 exact evaluator, or the M1636 sensitivity result.

## Supported Claims

M1640 supports:

```text
the projection repair module is implemented and focused-tested;
the M1636 scale_1e-3 candidate remains measurable;
gradient signal reaches actor_mean;
the no-checkpoint and role guardrails work;
the pre-registered Adam lr=1e-3 recipe fails to reduce residual under the trust metric.
```

## Unsupported Claims

M1640 does not support:

```text
projection repair works with the pre-registered recipe;
checkpoint artifact generation;
PPO proposal repair;
closed-loop behavior improvement;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

## Failure Taxonomy

Failure taxonomy:

```text
training_instability
```

This is projection/optimizer instability rather than environment training, but
it is the closest existing taxonomy label: the objective was connected, but the
optimizer step scale was unsuitable for the small actor_mean perturbation.

## Next Route

Route to mandatory result audit:

```text
m1641-paper-route-contour-aware-exact-objective-projection-repair-result-audit
```

The audit should decide whether to:

```text
design a step-size/backtracking projection repair;
switch from Adam to exact line-search or damped gradient projection;
pivot away from actor_mean-only projection;
or stop the public exact-objective repair branch as too brittle.
```

Do not rerun with a tuned learning rate inside M1640. The negative result is
part of the evidence chain and must be audited first.
