# M1642 Paper-Route Contour-Aware Damped Projection Repair Design

## Summary

M1642 designs a deterministic damped/backtracking projection repair after the
M1640 negative result and M1641 audit.

Decision:

```text
contour_aware_damped_projection_design_admit_bounded_implementation
```

This milestone is design-only. It does not run projection, train, run PPO, run
closed-loop evaluation, write checkpoint artifacts, promote, use private
holdout, change actor inputs, treat diagnostics as positive targets, treat
donor-plus actions as loss targets, or claim paper-level or level3
self-identification evidence.

## Blocker

M1640 showed that the exact-objective projection plumbing is connected but the
pre-registered Adam recipe is too aggressive:

```text
initial_positive_exact_residual_mean: 0.0003143580979667604
step 1 positive_exact_residual_mean:  0.03115139901638031
best post-step residual:              0.0005202809115871787
grad_norm_max:                        4.537821292877197
```

The first Adam step was approximately the same L2 scale as the entire
actor_mean perturbation and expanded the actor_mean distance to base:

```text
initial_actor_mean_l2_to_base: 0.019672319293022156
step 1 actor_mean_l2_to_base:  0.026685267686843872
```

So M1640 did not disprove projection. It disproved that unbounded Adam
`lr=1e-3` is a suitable local projection recipe for a `scale_1e-3` perturbation.

## Design Principle

The next implementation must be an exact full-batch projection, not a tuned
training run:

```text
PPO: blocked
closed-loop training/evaluation: blocked
checkpoint artifact: blocked
private holdout: blocked
actor input change: blocked
diagnostics as loss targets: blocked
```

It should treat M1640 as a local feasibility-restoration problem:

```text
given perturbed actor_mean theta_p
given base actor_mean theta_b
given materialized positive targets

find theta_r near theta_p
such that exact positive residual decreases
and actor_mean distance to theta_b does not expand
```

The implementation must write metrics only and route to audit before any
checkpoint artifact or PPO route.

## Fixed Inputs

Use the same fixed inputs as M1640:

```text
checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt

materialization:
  runs/m1630_contour_aware_full_target_materialization

candidate:
  M1636 scale_1e-3 actor_mean perturbation
  perturb_seed: 1639

positive rows:
  39

diagnostic rows:
  232
```

Do not alter observation contract, hidden tensors, source rows, target actions,
or diagnostic role weights.

## Optimization Scope

Trainable parameters:

```text
actor_mean.weight
actor_mean.bias
```

Frozen parameters:

```text
response_encoder
context_encoder
online_gru_cell
response_context_fusion
critic
log_std
sequence_tail
response_prediction_head
all auxiliary heads
```

Implementation must report:

```text
non_actor_mean_parameter_delta_max == 0.0
```

## Objective

Use the same role-safe M1632/M1638 objective over positive rows only:

```text
features_correct = recurrent_features_tensor(observation, correct_hidden)
features_wrong   = recurrent_features_tensor(observation, wrong_hidden)

a_correct = tanh(actor_mean(features_correct))
a_wrong   = tanh(actor_mean(features_wrong))

L =
    mean(||a_correct - preferred_action||^2)
  + mean(||a_wrong - wrong_history_action||^2)
  + 0.25 * mean(max(0, m_sep - ||a_correct - a_wrong||)^2)
```

Separation margin stays:

```text
m_sep = min(0.05, quantile_0.25(||preferred_action - wrong_history_action||))
```

Diagnostic rows are evaluated before/after and in candidate traces, but:

```text
diagnostic_rows_used_as_positive: false
diagnostic_positive_weight_sum: 0.0
diagnostic_gradient_weight: 0.0
```

Donor-plus actions remain diagnostic-only:

```text
donor_plus_action_used_as_loss_target: false
```

## Damped Backtracking Rule

M1643 should replace Adam with a deterministic full-batch backtracking
projection:

```text
max_projection_steps: 10
initial_step_fraction: 0.25
backtracking_factors:
  [1.0, 0.5, 0.25, 0.125, 0.0625, 0.03125, 0.015625]
direction:
  negative normalized full-batch gradient over actor_mean parameters
base_step_l2:
  initial_step_fraction * initial_actor_mean_l2_to_base
candidate_step_l2:
  base_step_l2 * backtracking_factor
```

For each projection step:

```text
1. compute full-batch exact loss and gradient at current theta
2. flatten actor_mean gradient g
3. if ||g|| is zero or nonfinite, stop with gradient_null_or_nonfinite
4. form direction d = -g / ||g||
5. try candidate theta' = theta + candidate_step_l2 * d for each backtracking factor
6. evaluate exact positive residual and actor_mean_l2_to_base for theta'
7. accept the first candidate satisfying acceptance rules below
8. if no factor is accepted, stop with no_backtracking_candidate_accepted
```

This is deterministic and not ad hoc learning-rate search: the candidate grid,
order, objective, trust metric, and stop criteria are pre-registered.

## Acceptance Rules

A backtracking candidate can be accepted only if all are true:

```text
candidate_positive_exact_residual_mean < current_positive_exact_residual_mean
candidate_actor_mean_l2_to_base <= current_actor_mean_l2_to_base
candidate_actor_mean_l2_to_base <= initial_actor_mean_l2_to_base
candidate_action_l2_max is finite
candidate_exact_residual is finite
non_actor_mean_parameter_delta_max == 0.0
```

Select the first accepted factor in the pre-registered order. Do not use
private holdout, closed-loop replay, or human judgment to select the candidate.

Stop when either:

```text
positive_exact_residual_reduction_ratio >= 0.50
or max_projection_steps reached
or no backtracking factor is accepted
or gradient is zero/nonfinite
```

## No Base Reset Rule

Because the target actions were generated by the base policy, resetting
`actor_mean` to the base would trivially pass and prove little.

Therefore M1643 must not use direct base interpolation as a repair candidate:

```text
base_interpolation_used_for_repair: false
```

Optional diagnostic-only interpolation is allowed if clearly labeled and never
used for acceptance:

```text
base_interpolation_diagnostic_written: optional
base_interpolation_diagnostic_used_for_repair: false
```

## Public-Row Overfit Guardrails

This branch is public-row exact-objective plumbing, not driver evidence.
M1643 must preserve:

```text
repaired_checkpoint_written: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
diagnostic_rows_used_as_positive: false
donor_plus_action_used_as_loss_target: false
```

Outputs should be metrics only:

```text
runs/m1643_contour_aware_damped_projection_repair/summary.json
runs/m1643_contour_aware_damped_projection_repair/projection_step_trace.csv
runs/m1643_contour_aware_damped_projection_repair/backtracking_candidate_trace.csv
runs/m1643_contour_aware_damped_projection_repair/repair_summary.csv
runs/m1643_contour_aware_damped_projection_repair/guardrail_summary.csv
```

No `.pt` files may appear under the run directory.

## Pass Thresholds

M1643 public smoke passes only if:

```text
initial_positive_exact_residual_mean > 1e-8
repaired_positive_exact_residual_mean < initial_positive_exact_residual_mean
positive_exact_residual_reduction_ratio >= 0.50
repaired_actor_mean_l2_to_base <= initial_actor_mean_l2_to_base
accepted_backtracking_step_count >= 1
non_actor_mean_parameter_delta_max == 0.0
repaired_checkpoint_written == false
guardrail_violation_count == 0
```

If the projection reduces residual but does not reach 50 percent reduction,
record:

```text
projection_partial_reduction
```

If no candidate is accepted, record:

```text
no_backtracking_candidate_accepted
```

If gradients are null/nonfinite, record:

```text
gradient_null_or_nonfinite
```

## Why This Is Still Not Driver Progress

Even if M1643 passes, it will only show:

```text
the exact objective can locally repair a controlled actor_mean perturbation;
the projection tool can be made step-size stable;
```

It will not show:

```text
PPO proposal repair works;
closed-loop avoidance improves;
wrong-history sensitivity is stronger;
the policy self-identifies hidden dynamics;
the checkpoint should be promoted.
```

Those require later closed-loop proof, generalization, and promotion gates.

## Decision

Admit exactly one bounded implementation:

```text
m1643-paper-route-contour-aware-damped-projection-repair-implementation
```

M1643 may implement and run only the pre-registered damped/backtracking
no-checkpoint projection probe. It must route to result audit afterward.
