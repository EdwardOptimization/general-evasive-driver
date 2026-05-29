# M1639 Paper-Route Contour-Aware Exact Objective Branch Synthesis

## Summary

M1639 synthesizes the M1629-M1638 contour-aware exact-objective sequence before
any projection implementation.

Synthesis decision:

```text
continue
```

Route decision:

```text
admit one bounded no-checkpoint projection implementation
```

This is process-only. It does not run actor update implementation, train, run
PPO, promote a checkpoint, use private holdout, change actor inputs, treat
diagnostics as positive targets, treat donor-plus actions as loss targets, or
claim level3 self-identification.

## Evidence Summary

M1629 designed full policy-target materialization after the M1628 synthesis.
It required separate positive and diagnostic tensor bundles, exact
source-action reproduction, checkpoint mutation guards, and no objective or
training artifacts.

M1630 implemented full materialization and passed:

```text
positive_policy_target_count: 39
diagnostic_policy_guardrail_count: 232
positive_observation_shape: [39, 72]
diagnostic_observation_shape: [232, 72]
hidden_dim: 128
source_action_l2_max: 0.0 for positive and diagnostic rows
missing_capture_row_count: 0
diagnostic_rows_used_as_positive: false
checkpoint_weights_mutated: false
passes_public_smoke_gates: true
```

M1631 audited that materialization and admitted objective design only.

M1632 designed same-observation correct/wrong hidden action residual semantics:

```text
correct history -> preferred_action
wrong history   -> wrong_history_action
separation collapse guard between the two branches
diagnostics remain zero-weight guardrails
donor_plus_hidden_action is diagnostic-only because donor_plus_observation was not persisted
```

M1633 implemented the no-update exact evaluator and passed:

```text
positive_policy_target_count: 39
diagnostic_policy_guardrail_count: 232
positive_policy_action_residual_l2_max: 0.0
diagnostic_policy_action_residual_l2_max: 0.0
positive_exact_residual_mean: 0.0
donor_plus_action_used_as_loss_target: false
diagnostic_rows_used_as_positive: false
checkpoint_weights_mutated: false
passes_public_smoke_gates: true
```

M1634 audited the zero-residual result and correctly rejected direct base
update as uninformative.

M1635 designed an in-memory sensitivity probe. M1636 implemented it and passed:

```text
candidate_count: 4
base_positive_exact_residual_mean: 0.0
base_positive_policy_action_residual_l2_max: 0.0
max_positive_exact_residual_mean_over_perturbations: 0.0003143580689195087
max_positive_policy_action_residual_l2_max_over_perturbations: 0.015652681982969475
measurable_perturbation_residual: true
perturbed_checkpoint_written: false
checkpoint_weights_mutated: false
passes_public_smoke_gates: true
```

M1637 audited M1636 and admitted projection design. M1638 designed an
`actor_mean`-only projection repair probe but routed here before implementation
because the branch hit synthesis cadence.

## Supported Claims

The branch now supports:

```text
the public positive/diagnostic package can be materialized into policy-side tensors;
the exact evaluator can reproduce base deterministic actions exactly;
diagnostics remain zero-weight guardrails through materialization and evaluation;
donor-plus actions are correctly excluded from loss targets;
the exact objective detects controlled actor_mean policy-output drift;
a bounded no-checkpoint projection implementation is meaningful as a plumbing test.
```

## Falsified Or Rejected Claims

The branch rejects:

```text
metadata-only row metrics are enough for policy repair;
direct base update is meaningful when exact residual is zero;
donor_plus_hidden_action can be trained without donor_plus_observation;
public exact-objective success proves closed-loop behavior;
public exact-objective success proves level3 self-identification;
PPO or checkpoint promotion is admitted by this branch.
```

No current result falsifies the projection idea. It only remains unimplemented.

## Failure Taxonomy Summary

Failure taxonomy remains:

```text
none
```

The important non-failure caveats are:

```text
M1633 base residual is zero by construction;
M1636 perturbations are controlled actor_mean drifts, not PPO proposals;
all evidence is public-row exact-objective plumbing;
no closed-loop replay or generalization gate has been run on repaired candidates.
```

## Public-Gate Overfit Risk

Public-gate overfit risk is high:

```text
positive target count is 39;
diagnostic rows are public guardrails, not private validation;
the exact objective currently restores base actions rather than discovering new behavior;
projection could become a public-row memorizer if it writes/promotes checkpoints too early.
```

Mitigation:

```text
allow only one bounded no-checkpoint projection implementation;
optimize only actor_mean in memory;
do not write .pt outputs;
do not run closed-loop promotion gates yet;
route implementation to audit before any checkpoint artifact or PPO design;
continue to treat diagnostics and donor-plus actions as guardrails only.
```

## Next Branch Decision

Decision:

```text
continue
```

Next task:

```text
m1640-paper-route-contour-aware-exact-objective-projection-repair-implementation
```

M1640 may implement exactly one bounded in-memory projection probe:

```text
input candidate: M1636 scale_1e-3 actor_mean perturbation;
repair scope: actor_mean.weight and actor_mean.bias only;
target: reduce positive exact residual;
output: metrics only, no checkpoint;
follow-up: mandatory result audit before any further repair, checkpoint artifact, PPO, or promotion route.
```

Blocked:

```text
training;
PPO;
promotion;
private holdout;
actor input changes;
paper-level claims;
level3 self-identification claims.
```
