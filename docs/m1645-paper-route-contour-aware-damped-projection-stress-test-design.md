# M1645 Paper-Route Contour-Aware Damped Projection Stress Test Design

## Summary

M1645 designs a no-checkpoint perturbation stress test for the M1643
damped/backtracking projection rule.

Decision:

```text
contour_aware_damped_projection_stress_design_admit_bounded_implementation
```

This is design-only. It does not run projection, train, run PPO, run
closed-loop evaluation, write checkpoint artifacts, promote, use private
holdout, change actor inputs, treat diagnostics as positive targets, treat
donor-plus actions as loss targets, or claim paper-level or level3
self-identification evidence.

## Motivation

M1643 proved that damped/backtracking projection can repair one controlled
M1636-style actor_mean perturbation:

```text
scale: 1e-3
seed: 1639
positive_exact_residual_reduction_ratio: 0.8982656378486144
accepted_backtracking_step_count: 1
guardrail_violation_count: 0
```

That is enough to show local projection plumbing works. It is not enough to
write a checkpoint artifact or claim readiness for PPO-proposal repair. Before
using the projection tool on a more meaningful candidate, it should survive a
small deterministic stress grid.

## Fixed Inputs

Use:

```text
checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt

materialization:
  runs/m1630_contour_aware_full_target_materialization

projection module:
  autodrift.contour_aware_exact_objective_projection_repair

projection mode:
  damped_backtracking
```

No actor-input, target, materialization, role, or diagnostic schema changes are
allowed.

## Stress Grid

M1646 should run exactly these nonzero stress candidates:

```text
perturb_scales:
  [1e-4, 3e-4, 1e-3]

perturb_seeds:
  [1645, 1646, 1647]
```

Total stress candidates:

```text
9
```

Do not add or remove grid points after seeing results. Do not include `scale=0`
as a pass candidate; base-zero behavior is already covered by M1633/M1636 and
would dilute the stress summary.

## Per-Candidate Projection Rule

Each candidate uses the M1642/M1643 damped projection configuration:

```text
max_projection_steps: 10
initial_step_fraction: 0.25
backtracking_factors:
  [1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625]
gradient scope:
  actor_mean.weight
  actor_mean.bias
loss:
  positive exact residual only
diagnostics:
  zero-weight evaluation only
donor_plus:
  excluded from loss target
base_interpolation_used_for_repair:
  false
checkpoint output:
  none
```

Each candidate writes to:

```text
runs/m1646_contour_aware_damped_projection_stress_test/candidates/scale_<scale>_seed_<seed>/
```

Each candidate sub-run should contain the same no-checkpoint artifacts as
M1643:

```text
summary.json
projection_step_trace.csv
backtracking_candidate_trace.csv
repair_summary.csv
guardrail_summary.csv
```

## Aggregate Outputs

M1646 should write:

```text
runs/m1646_contour_aware_damped_projection_stress_test/summary.json
runs/m1646_contour_aware_damped_projection_stress_test/candidate_summary.csv
runs/m1646_contour_aware_damped_projection_stress_test/aggregate_summary.csv
runs/m1646_contour_aware_damped_projection_stress_test/guardrail_summary.csv
```

Suggested candidate summary columns:

```text
candidate_id
perturb_scale
perturb_seed
candidate_run_dir
initial_positive_exact_residual_mean
repaired_positive_exact_residual_mean
positive_exact_residual_reduction_ratio
initial_positive_action_l2_max
repaired_positive_action_l2_max
initial_actor_mean_l2_to_base
repaired_actor_mean_l2_to_base
accepted_backtracking_step_count
backtracking_candidate_count
projection_stop_reason
passes_public_smoke_gates
null_result_classification
guardrail_violation_count
repaired_checkpoint_written
base_interpolation_used_for_repair
```

## Aggregate Pass Criteria

The stress test passes only if:

```text
stress_candidate_count == 9
measurable_initial_residual_count == 9
residual_reduced_count == 9
candidate_public_pass_count >= 8
accepted_backtracking_candidate_count >= 8
min_positive_exact_residual_reduction_ratio >= 0.25
median_positive_exact_residual_reduction_ratio >= 0.50
max_guardrail_violation_count == 0
checkpoint_artifact_count == 0
base_interpolation_used_for_repair_count == 0
diagnostic_rows_used_as_positive_count == 0
donor_plus_action_used_as_loss_target_count == 0
training_started_count == 0
ppo_used_count == 0
promoted_count == 0
private_holdout_used_count == 0
actor_input_contract_changed_count == 0
level3_self_id_claim_count == 0
```

This deliberately permits one candidate to miss the full 50 percent reduction
gate while still requiring every candidate to reduce residual and preserve all
guardrails.

## Failure Classifications

Use candidate-level classifications from the projection module. Aggregate-level
classifications:

```text
damped_projection_stress_public_pass
stress_candidate_count_mismatch
nonmeasurable_initial_residual
residual_not_reduced
candidate_pass_count_below_threshold
accepted_backtracking_count_below_threshold
reduction_ratio_below_threshold
guardrail_violation
checkpoint_artifact_written
base_interpolation_repair_violation
```

Do not reinterpret partial reduction as success unless the aggregate criteria
above pass.

## Public-Row Overfit Boundary

This stress test still uses public fixed tensors:

```text
39 positive rows
232 diagnostic rows
same base checkpoint
same exact action targets
```

Therefore a pass can only claim:

```text
damped projection is stable over a small controlled actor_mean perturbation grid;
```

It cannot claim:

```text
checkpoint readiness;
PPO repair readiness;
closed-loop behavior improvement;
promotion;
paper-level evidence;
level3 self-identification.
```

## Next Route

Admit exactly one bounded implementation:

```text
m1646-paper-route-contour-aware-damped-projection-stress-test-implementation
```

M1646 may implement and run the pre-registered stress test only. It must route
to result audit afterward before any checkpoint artifact, PPO-proposal repair,
closed-loop route, promotion, private holdout, actor-input change, or level3
self-ID claim.
