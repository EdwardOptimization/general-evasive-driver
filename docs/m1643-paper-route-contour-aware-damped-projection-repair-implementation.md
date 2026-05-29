# M1643 Paper-Route Contour-Aware Damped Projection Repair Implementation

## Summary

M1643 implemented and ran the M1642 deterministic damped/backtracking
projection repair.

Decision:

```text
contour_aware_damped_projection_public_pass_route_to_audit
```

The damped projection repaired the controlled M1636 `scale_1e-3` actor_mean
perturbation without writing a checkpoint and without violating role
guardrails.

This is still an objective-sanity result only. It does not run PPO,
closed-loop training/evaluation, promotion, private holdout, actor-input
changes, or level3 self-identification claims.

## Implementation

Updated:

```text
src/autodrift/contour_aware_exact_objective_projection_repair.py
tests/test_contour_aware_exact_objective_projection_repair.py
```

New mode:

```text
--projection-mode damped_backtracking
```

The implementation preserves the original Adam mode for M1640 reproducibility,
and adds:

```text
projection_step_trace.csv
backtracking_candidate_trace.csv
accepted_backtracking_step_count
base_interpolation_used_for_repair
projection_stop_reason
```

## Validation

Focused test:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q tests/test_contour_aware_exact_objective_projection_repair.py
```

Result:

```text
3 passed in 3.11s
```

Official M1643 run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.contour_aware_exact_objective_projection_repair \
  --materialization-run-dir runs/m1630_contour_aware_full_target_materialization \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --run-dir runs/m1643_contour_aware_damped_projection_repair \
  --projection-mode damped_backtracking
```

Artifacts:

```text
runs/m1643_contour_aware_damped_projection_repair/summary.json
runs/m1643_contour_aware_damped_projection_repair/projection_step_trace.csv
runs/m1643_contour_aware_damped_projection_repair/backtracking_candidate_trace.csv
runs/m1643_contour_aware_damped_projection_repair/repair_summary.csv
runs/m1643_contour_aware_damped_projection_repair/guardrail_summary.csv
```

## Result

M1643 passed the public objective-sanity smoke:

```text
passes_public_smoke_gates: true
null_result_classification: contour_aware_exact_objective_projection_repair_public_pass
```

Key metrics:

```text
initial_positive_exact_residual_mean:  0.0003143580979667604
repaired_positive_exact_residual_mean: 0.00003198102058377117
positive_exact_residual_reduction:     0.00028237707738298923
positive_exact_residual_reduction_ratio: 0.8982656378486144

initial_positive_action_l2_max:  0.015652701258659363
repaired_positive_action_l2_max: 0.005414916668087244

initial_actor_mean_l2_to_base:  0.019672319293022156
repaired_actor_mean_l2_to_base: 0.019625606015324593
actor_mean_l2_reduction:       0.00004671327769756317

accepted_backtracking_step_count: 1
backtracking_candidate_count: 3
projection_stop_reason: target_reduction_reached
base_interpolation_used_for_repair: false
```

Diagnostics also improved, but they stayed zero-weight guardrails:

```text
initial_diagnostic_exact_residual_mean:  0.0002680706384126097
repaired_diagnostic_exact_residual_mean: 0.000035363835195312276
```

This diagnostic improvement is useful for auditing, but it is not a loss target.

## Backtracking Trace

Step 1 tried the pre-registered factors in order:

```text
factor 1.0:
  step_l2: 0.004918079823255539
  residual: 0.0026217380072921515
  accepted: false
  reason: residual_not_reduced

factor 0.5:
  step_l2: 0.0024590399116277695
  residual: 0.00032075721537694335
  accepted: false
  reason: residual_not_reduced

factor 0.25:
  step_l2: 0.0012295199558138847
  residual: 0.00003198102058377117
  actor_mean_l2_to_base: 0.019625606015324593
  accepted: true
```

The accepted candidate both reduced exact residual and preserved the actor_mean
trust region. This directly addresses the M1640 optimizer-step instability.

## Guardrails

Clean guardrails:

```text
repaired_checkpoint_written: false
checkpoint_weights_mutated: false
non_actor_mean_parameter_delta_max: 0.0
base_interpolation_used_for_repair: false
diagnostic_rows_used_as_positive: false
diagnostic_positive_weight_sum: 0
donor_plus_action_used_as_loss_target: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
guardrail_violation_count: 0
```

## Supported Claims

M1643 supports:

```text
damped/backtracking projection is step-size stable on the controlled M1636 perturbation;
the exact objective can locally reduce actor_mean policy-output residual;
one accepted full-batch gradient step can reduce positive residual by about 89.8%;
the repair can preserve the actor_mean trust region;
no-checkpoint and role guardrails are enforced.
```

## Unsupported Claims

M1643 still does not support:

```text
checkpoint artifact generation;
PPO proposal repair;
closed-loop avoidance improvement;
wrong-history proof strengthening in rollout;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

## Next Route

Route to mandatory result audit:

```text
m1644-paper-route-contour-aware-damped-projection-repair-result-audit
```

The audit should decide whether this projection tool is now ready for a
checkpoint-artifact design, a PPO-proposal repair design, another public-row
projection stress test, or branch synthesis. No checkpoint artifact or PPO
route is admitted by M1643 itself.
