# M1638 Paper-Route Contour-Aware Exact Objective Projection Repair Design

## Summary

M1638 designs a bounded projection/repair probe for the contour-aware exact
objective after the M1636 sensitivity pass and M1637 audit.

Decision:

```text
contour_aware_projection_repair_design_route_to_branch_synthesis
```

This milestone is design-only. It does not run actor update, does not train,
does not run PPO, does not promote a checkpoint, does not use private holdout,
does not change actor inputs, does not treat diagnostics or donor-plus actions
as positive targets, and does not claim level3 self-identification.

## Problem

M1636 proved that the exact objective detects controlled `actor_mean`
policy-output drift:

```text
base_positive_exact_residual_mean: 0.0
base_positive_policy_action_residual_l2_max: 0.0
max_positive_exact_residual_mean_over_perturbations: 0.0003143580689195087
max_positive_policy_action_residual_l2_max_over_perturbations: 0.015652681982969475
perturbed_checkpoint_written: false
```

The next question is narrower than driver improvement:

```text
Can the exact objective pull a controlled perturbed policy back toward the
materialized action targets without violating role or checkpoint guardrails?
```

This is a projection/repair plumbing question, not a closed-loop driving claim.

## Proposed Probe

Use the M1636 `scale_1e-3` perturbation recipe as the input candidate:

```text
base checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
materialization: runs/m1630_contour_aware_full_target_materialization
perturbation seed: same deterministic scheme as M1636
perturbation scope: actor_mean.weight and actor_mean.bias only
perturbation scale: 1e-3
```

Then run a no-deployment repair on an in-memory copy:

```text
freeze response_encoder
freeze context_encoder
freeze online_gru_cell
freeze response_context_fusion
freeze critic
freeze log_std
freeze auxiliary heads
optimize only actor_mean.weight and actor_mean.bias
```

The differentiable target is:

```text
features_correct = recurrent_features_tensor(observation, correct_hidden)
features_wrong   = recurrent_features_tensor(observation, wrong_hidden)

a_correct = tanh(actor_mean(features_correct))
a_wrong   = tanh(actor_mean(features_wrong))

L_positive =
    mean(||a_correct - preferred_action||^2)
  + mean(||a_wrong - wrong_history_action||^2)
  + 0.25 * mean(max(0, m_sep - ||a_correct - a_wrong||)^2)
```

Use only positive rows for optimization. Diagnostic rows are evaluated before
and after repair but carry zero gradient and zero positive weight.

## Bounded Configuration

Initial implementation should be a small projection smoke:

```text
optimizer: Adam
learning_rate: 1e-3
steps: 25
batching: full positive set, N=39
gradient scope: actor_mean only
trust_region_reference: unperturbed base actor_mean
trust_region_metric: repaired_actor_mean_l2_to_base <= initial_perturbed_l2_to_base
checkpoint output: none
```

No checkpoint should be written in the first projection probe. If later work
needs an artifact, write only metrics and optionally an in-memory candidate
hash; do not write `.pt` until a separate promotion-unsafe checkpoint-artifact
design exists.

## Metrics

Report before/after:

```text
initial_positive_exact_residual_mean
repaired_positive_exact_residual_mean
positive_exact_residual_reduction
positive_exact_residual_reduction_ratio
initial_positive_action_l2_max
repaired_positive_action_l2_max
initial_diagnostic_exact_residual_mean
repaired_diagnostic_exact_residual_mean
initial_actor_mean_l2_to_base
repaired_actor_mean_l2_to_base
repair_steps
grad_norm_max
non_actor_mean_parameter_delta_max
checkpoint_weights_mutated
repaired_checkpoint_written
```

Pass thresholds for a first smoke:

```text
initial_positive_exact_residual_mean > 1e-8
repaired_positive_exact_residual_mean < initial_positive_exact_residual_mean
positive_exact_residual_reduction_ratio >= 0.50
repaired_actor_mean_l2_to_base <= initial_actor_mean_l2_to_base
non_actor_mean_parameter_delta_max == 0.0
repaired_checkpoint_written == false
```

These thresholds prove only that projection mechanics work. They do not prove
closed-loop behavior or PPO repair.

## Guardrails

The projection probe must keep:

```text
actor_update_is_projection_probe_only=true
training_started=false
ppo_used=false
promoted=false
private_holdout_used=false
actor_input_contract_changed=false
diagnostic_rows_used_as_positive=false
diagnostic_positive_weight_sum=0.0
donor_plus_action_used_as_loss_target=false
labels_enter_actor_input=false
level3_self_id_claim_made=false
```

If any guardrail fails, the result is `contract_violation` or `objective_overfit`
depending on the failure.

## Why This Is Not Yet Driver Progress

The projection target is the same base action target that generated M1630.
Therefore a successful projection only shows:

```text
the exact objective can restore a controlled local actor_mean perturbation;
the evaluator can become a retention/projection tool;
```

It does not show:

```text
closed-loop avoidance improved;
wrong-history evidence strengthened;
GRU self-identification is proven;
PPO proposal repair works;
the checkpoint should be promoted.
```

## Synthesis Requirement

This branch has now accumulated another narrow design/implementation/audit
sequence after the M1628 synthesis:

```text
M1629-M1638
```

Per harness cadence, do not implement the projection probe immediately. Route
to branch synthesis first. The synthesis should decide whether to continue to
one bounded projection implementation, pivot away from public exact-objective
repair, or stop the branch as too public-row-specific.

## Decision

Route to branch synthesis:

```text
m1639-paper-route-contour-aware-exact-objective-branch-synthesis
```

PPO, promotion, private holdout, actor-input changes, and paper-level claims
remain blocked.
