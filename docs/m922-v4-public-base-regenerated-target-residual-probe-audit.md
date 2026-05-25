# M922 V4 Public-Base Regenerated-Target Residual Probe Audit

## Purpose

M922 audits the M921 no-candidate result and selects the next route.

M922 is audit-only:

```text
no new training
no M880 exact compatibility
no replay
no PPO
no checkpoint promotion
```

## Audit Finding

M921 is not blocked by infrastructure:

```text
sample_reconstruction_success_rate: 1.0
missing_target_keys: 0
actor_backbone_changed: false
training_started: true
residual_only_training: true
```

It is blocked by objective geometry:

```text
target-action loss improves
low-tail metrics improve only at larger alpha
normal retention fails at larger alpha
normal-retaining alphas do not produce enough tail lift
```

This means the current loss is too indirect. It learns a residual direction
that points partially toward the desired targets, but the low-tail improvement
needed by the registered gate is not achieved inside the trust region.

## Failure Classification

Classification:

```text
objective_overfit
```

Reason:

```text
The optimized target-action objective improves its direct target metric, but
the full objective gate requiring normal-retained low-tail lift does not pass.
```

This is not:

```text
contract_violation
lineage_invalid
training_instability
metric_artifact
proof_washout
```

## Quantitative Summary

Best target-loss alpha:

```text
alpha: 1.0
target_action_mse_mean: 0.0004428685
target_loss_pass: true
tail_lift_pass: false
normal_retention_pass: false
```

Best normal-retaining alpha by movement:

```text
alpha: 0.35
target_loss_pass: true
tail_lift_pass: false
normal_retention_pass: true
low_tail_fraction: 0.39323992
```

Candidate threshold that remains unmet at alpha `0.35`:

```text
required low_tail_fraction <= 0.36055235
observed low_tail_fraction = 0.39323992
```

## Route

The next step should not be exact compatibility or replay. M921 has no admitted
objective alpha.

The next route is:

```text
m923-v4-public-base-alpha-aware-low-tail-objective-design
```

M923 should design an alpha-aware objective that optimizes the metrics that
blocked M921 directly:

```text
normal-retaining alpha range;
low-tail p10 lift;
low-tail fraction reduction;
gap-deficit reduction;
target-action alignment as an auxiliary, not the only main objective.
```

## Safeguards

M923 should preserve:

```text
M399 actor backbone frozen;
P0 human-view actor input contract unchanged;
M919 targets as training-time data only;
M880 exact compatibility blocked until objective alpha passes;
replay/PPO/promotion blocked until exact compatibility passes.
```

## Decision

Decision:

```text
regenerated_target_residual_probe_audit_route_to_alpha_aware_low_tail_objective_design
```

Next:

```text
m923-v4-public-base-alpha-aware-low-tail-objective-design
```
