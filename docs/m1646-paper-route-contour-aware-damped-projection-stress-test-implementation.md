# M1646 Paper-Route Contour-Aware Damped Projection Stress Test Implementation

## Summary

M1646 implemented and ran the no-checkpoint stress test designed in M1645.

Decision:

```text
contour_aware_damped_projection_stress_public_pass_route_to_audit
```

The fixed 9-candidate stress grid passed all aggregate gates. No checkpoint was
written, no PPO or closed-loop evaluation ran, no actor input changed, and
diagnostics remained zero-weight.

This is still fixed-tensor exact-objective infrastructure evidence, not
checkpoint, PPO, closed-loop, promotion, private-holdout, paper-level, or
level3 self-identification evidence.

## Implementation

Added:

```text
src/autodrift/contour_aware_exact_objective_projection_stress_test.py
tests/test_contour_aware_exact_objective_projection_stress_test.py
```

The stress runner calls the existing no-checkpoint repair module with:

```text
projection_mode: damped_backtracking
scales: [1e-4, 3e-4, 1e-3]
seeds: [1645, 1646, 1647]
candidate_count: 9
```

Each candidate writes its own M1643-style artifacts under:

```text
runs/m1646_contour_aware_damped_projection_stress_test/candidates/
```

The aggregate runner writes:

```text
runs/m1646_contour_aware_damped_projection_stress_test/summary.json
runs/m1646_contour_aware_damped_projection_stress_test/candidate_summary.csv
runs/m1646_contour_aware_damped_projection_stress_test/aggregate_summary.csv
runs/m1646_contour_aware_damped_projection_stress_test/guardrail_summary.csv
```

## Validation

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q \
  tests/test_contour_aware_exact_objective_projection_repair.py \
  tests/test_contour_aware_exact_objective_projection_stress_test.py
```

Result:

```text
5 passed in 3.15s
```

Official M1646 run:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.contour_aware_exact_objective_projection_stress_test \
  --materialization-run-dir runs/m1630_contour_aware_full_target_materialization \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --run-dir runs/m1646_contour_aware_damped_projection_stress_test
```

## Aggregate Result

M1646 passed:

```text
passes_public_smoke_gates: true
null_result_classification: damped_projection_stress_public_pass
```

Aggregate metrics:

```text
stress_candidate_count: 9
expected_stress_candidate_count: 9
measurable_initial_residual_count: 9
residual_reduced_count: 9
candidate_public_pass_count: 9
accepted_backtracking_candidate_count: 9

min_positive_exact_residual_reduction_ratio:    0.7070986860856349
median_positive_exact_residual_reduction_ratio: 0.7420973915926545
max_positive_exact_residual_reduction_ratio:    0.8632753818236488
```

Guardrails:

```text
max_guardrail_violation_count: 0
checkpoint_artifact_count: 0
base_interpolation_used_for_repair_count: 0
diagnostic_rows_used_as_positive_count: 0
donor_plus_action_used_as_loss_target_count: 0
training_started_count: 0
ppo_used_count: 0
promoted_count: 0
private_holdout_used_count: 0
actor_input_contract_changed_count: 0
level3_self_id_claim_count: 0
```

## Candidate Summary

All candidates passed the per-candidate public gate:

```text
scale_1em04_seed_1645 reduction ratio: 0.8632735541879808
scale_1em04_seed_1646 reduction ratio: 0.741882253502812
scale_1em04_seed_1647 reduction ratio: 0.7101151893188341

scale_3em04_seed_1645 reduction ratio: 0.8632753818236488
scale_3em04_seed_1646 reduction ratio: 0.7420973915926545
scale_3em04_seed_1647 reduction ratio: 0.7094369457454098

scale_1em03_seed_1645 reduction ratio: 0.8632351467488777
scale_1em03_seed_1646 reduction ratio: 0.7427829830993862
scale_1em03_seed_1647 reduction ratio: 0.7070986860856349
```

Every candidate accepted exactly one damped backtracking step and stopped with:

```text
target_reduction_reached
```

## Supported Claims

M1646 supports:

```text
damped projection is stable across the pre-registered 3x3 actor_mean perturbation grid;
all fixed-grid candidates reduce exact residual;
all fixed-grid candidates pass no-checkpoint role guardrails;
aggregate exact-objective projection infrastructure is ready for audit.
```

## Unsupported Claims

M1646 still does not support:

```text
checkpoint artifact generation;
PPO-proposal repair;
closed-loop replay improvement;
behavior retention;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

## Next Route

Route to mandatory audit:

```text
m1647-paper-route-contour-aware-damped-projection-stress-test-result-audit
```

The audit should decide whether the projection branch should proceed to:

```text
checkpoint-artifact design;
PPO-proposal repair design;
branch synthesis;
or a broader non-public stress route.
```

No such route is admitted directly by M1646.
