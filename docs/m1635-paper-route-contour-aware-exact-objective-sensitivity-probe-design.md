# M1635 Paper-Route Contour-Aware Exact Objective Sensitivity Probe Design

## Summary

M1635 designs a bounded sensitivity probe for the M1633 exact objective.

Decision:

```text
contour_aware_exact_objective_sensitivity_design_admit_bounded_implementation
```

This milestone is design-only. It does not run actor update, does not train,
does not run PPO, does not promote a checkpoint, does not use private holdout,
does not change actor inputs, and does not claim level3 self-identification.

## Problem

M1633 shows the exact evaluator is clean, but it also shows a zero-residual
base:

```text
positive_exact_residual_mean: 0.0
positive_policy_action_residual_l2_max: 0.0
```

That is expected because the M1630 tensors were captured from the same base
checkpoint. A direct objective-only actor update from this base would be
uninformative. Before any repair/projection update is designed, the exact
objective must first prove it can detect controlled deviations from the base.

## Probe Scope

M1636 should be an evaluation-only sensitivity implementation:

```text
load base checkpoint;
evaluate exact objective at scale 0.0;
create in-memory perturbed model copies;
evaluate exact objective for each perturbation scale;
write sensitivity artifacts;
do not write perturbed checkpoints;
do not run gradient update;
do not train;
do not promote.
```

Perturbation scope:

```text
actor_mean.weight
actor_mean.bias
```

Do not perturb recurrent encoders, context encoders, critic, auxiliary heads,
or `log_std` in the first probe. The goal is to test whether the exact action
target evaluator is sensitive to controlled deterministic policy output drift,
not to test representation fragility.

Perturbation plan:

```text
seed: 1636
scales: 0.0, 1e-4, 3e-4, 1e-3
noise: deterministic standard normal normalized per tensor
mode: in-memory clone only
```

## Metrics

For each candidate scale, M1636 should report:

```text
positive_exact_residual_mean
positive_policy_action_residual_l2_max
positive_policy_action_residual_l2_mean
diagnostic_exact_residual_mean
diagnostic_policy_action_residual_l2_max
positive_target_sep_l2_min
positive_policy_sep_l2_min
diagnostic_rows_used_as_positive
donor_plus_action_used_as_loss_target
checkpoint_weights_mutated
perturbed_checkpoint_written
```

The base candidate should match M1633:

```text
scale=0.0 positive_exact_residual_mean == 0.0
scale=0.0 positive_policy_action_residual_l2_max <= 1e-6
```

At least one perturbed candidate should produce measurable objective movement:

```text
max_positive_exact_residual_mean_over_perturbations > 1e-8
max_positive_policy_action_residual_l2_max_over_perturbations > 1e-5
```

The exact thresholds are intentionally weak. M1636 is a sensitivity smoke, not
a repair result. Stronger thresholds should only be set after observing the
first bounded response.

## Guardrails

M1636 must preserve these guardrails:

```text
base_checkpoint_sha256_before == base_checkpoint_sha256_after
perturbed_checkpoint_written == false
actor_update_run == false
training_started == false
ppo_used == false
promoted == false
private_holdout_used == false
actor_input_contract_changed == false
diagnostic_rows_used_as_positive == false
donor_plus_action_used_as_loss_target == false
level3_self_id_claim_made == false
```

The in-memory perturbation is a candidate-evaluation device, not a trained
checkpoint and not a promoted policy.

## Pass/Fail Interpretation

Pass means:

```text
the exact objective detects controlled deterministic policy-output drift;
base remains zero-residual;
guardrails are clean;
the project may design a bounded projection/repair probe next.
```

Fail means:

```text
if base residual is nonzero, the evaluator or materialization is inconsistent;
if perturbation residuals remain zero, the perturbation scope is ineffective;
if guardrails fail, sensitivity implementation must be repaired before any update design.
```

## Unsupported Claims

M1635 does not support:

```text
objective-only repair works;
actor update is safe;
PPO proposal can be repaired;
closed-loop behavior improved;
checkpoint promotion is admitted;
paper-level validation is available;
the driver has level3 self-identification.
```

## Decision

Admit one bounded sensitivity implementation:

```text
m1636-paper-route-contour-aware-exact-objective-sensitivity-probe-implementation
```

Do not route directly to actor update, PPO, promotion, private holdout, or
paper-level claims.
