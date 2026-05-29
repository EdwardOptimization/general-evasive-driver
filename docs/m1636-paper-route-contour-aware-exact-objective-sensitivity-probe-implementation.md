# M1636 Paper-Route Contour-Aware Exact Objective Sensitivity Probe Implementation

## Summary

M1636 implements and runs the no-update sensitivity probe designed in M1635.

Decision:

```text
contour_aware_exact_objective_sensitivity_probe_public_pass_route_to_audit
```

This is infrastructure only. It evaluates the exact objective on the
zero-residual base and in-memory `actor_mean` perturbations. It does not write
perturbed checkpoints, run gradient update, train, run PPO, promote a
checkpoint, use private holdout, change actor inputs, or claim level3
self-identification.

## Implementation

New files:

```text
src/autodrift/contour_aware_exact_objective_sensitivity_probe.py
tests/test_contour_aware_exact_objective_sensitivity_probe.py
```

The probe:

```text
loads the base checkpoint once;
deep-copies the model in memory for each candidate;
perturbs only actor_mean.weight and actor_mean.bias;
reuses the M1633 exact evaluator for each candidate;
writes aggregate sensitivity artifacts;
never writes a perturbed .pt file.
```

## Commands

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_contour_aware_exact_objective_sensitivity_probe.py
```

Result:

```text
2 passed in 2.05s
```

Sensitivity probe:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.contour_aware_exact_objective_sensitivity_probe --materialization-run-dir runs/m1630_contour_aware_full_target_materialization --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt --run-dir runs/m1636_contour_aware_exact_objective_sensitivity_probe
```

Result:

```text
base_positive_exact_residual_mean=0.0
base_positive_policy_action_residual_l2_max=0.0
max_positive_exact_residual_mean_over_perturbations=0.0003143580689195087
max_positive_policy_action_residual_l2_max_over_perturbations=0.015652681982969475
passes_public_smoke_gates=True
null_result_classification=contour_aware_exact_objective_sensitivity_probe_public_pass
```

## Artifacts

```text
runs/m1636_contour_aware_exact_objective_sensitivity_probe/summary.json
runs/m1636_contour_aware_exact_objective_sensitivity_probe/candidate_summary.csv
runs/m1636_contour_aware_exact_objective_sensitivity_probe/guardrail_summary.csv
runs/m1636_contour_aware_exact_objective_sensitivity_probe/candidates/scale_0e00/summary.json
runs/m1636_contour_aware_exact_objective_sensitivity_probe/candidates/scale_1em04/summary.json
runs/m1636_contour_aware_exact_objective_sensitivity_probe/candidates/scale_3em04/summary.json
runs/m1636_contour_aware_exact_objective_sensitivity_probe/candidates/scale_1em03/summary.json
```

## Result

Summary:

```text
candidate_count: 4
base_positive_exact_residual_mean: 0.0
base_positive_policy_action_residual_l2_max: 0.0
base_residual_near_zero: true
max_positive_exact_residual_mean_over_perturbations: 0.0003143580689195087
max_positive_policy_action_residual_l2_max_over_perturbations: 0.015652681982969475
measurable_perturbation_residual: true
perturbed_checkpoint_written: false
checkpoint_weights_mutated: false
actor_update_run: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

Candidate response:

```text
scale 0.0:   positive residual mean 0.0,       l2 max 0.0
scale 1e-4:  positive residual mean 2.91e-06,  l2 max 0.001963
scale 3e-4:  positive residual mean 9.52e-05,  l2 max 0.007549
scale 1e-3:  positive residual mean 3.14e-04,  l2 max 0.015653
```

The perturbed candidates fail the M1633 zero-residual evaluator gate, as
expected. M1636 passes because the aggregate sensitivity gate requires the base
to remain zero and at least one perturbed candidate to become measurably
nonzero.

No `.pt` files were written under the run directory.

## Interpretation

M1636 proves the exact objective is sensitive to controlled deterministic
policy-output drift. That makes it plausible as a future retention/projection
metric. It still does not prove that a repair step works; it only proves the
metric detects the kind of drift that a repair step would need to reduce.

## Validation

```text
make research-validate: passed
python -m compileall -q src tests: passed
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q:
  1612 passed, 4 warnings in 7.38s
```

## Unsupported Claims

M1636 does not support:

```text
objective-only repair works;
actor update is safe;
PPO proposal can be repaired;
closed-loop behavior improved;
checkpoint promotion is admitted;
private-holdout evidence;
paper-level validation;
level3 anticipatory self-identification.
```

## Next

Route to result audit before any repair/projection design:

```text
m1637-paper-route-contour-aware-exact-objective-sensitivity-probe-result-audit
```
