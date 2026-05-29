# M1648 Paper-Route Contour-Aware Damped Projection Branch Synthesis

## Summary

M1648 synthesizes the M1640-M1647 local damped-projection branch before any
checkpoint artifact, PPO-proposal repair, closed-loop evaluation, or further
local projection implementation.

Synthesis decision:

```text
promote_to_next_branch
```

Route decision:

```text
admit design-only PPO-proposal damped projection repair planning
```

This is process-only. It does not rerun projection, train, run PPO, evaluate
closed-loop behavior, write a checkpoint, promote, use private holdout, change
actor inputs, treat diagnostics as positive targets, treat donor-plus actions
as loss targets, or claim paper-level or level3 self-identification evidence.

## Evidence Summary

M1640 implemented the first bounded no-checkpoint projection probe over the
M1630 contour-aware materialized tensors:

```text
scope: actor_mean.weight and actor_mean.bias only
input candidate: M1636 scale_1e-3 controlled actor_mean perturbation
checkpoint written: false
diagnostic rows used as positive: false
donor_plus_action used as loss target: false
```

The module and focused tests worked, and gradients reached `actor_mean`, but
the pre-registered Adam `lr=1e-3` step was unstable:

```text
initial positive exact residual mean:  0.0003143580979667604
repaired positive exact residual mean: 0.0003143580979667604
positive exact residual reduction ratio: 0.0
passes public smoke gates: false
failure taxonomy: training_instability
```

M1641 audited that as optimizer-step instability rather than materialization or
exact-evaluator failure, and admitted damped/backtracking design.

M1642 designed a normalized full-batch damped projection rule. M1643
implemented it and passed the local objective-sanity gate:

```text
initial positive exact residual mean:  0.0003143580979667604
repaired positive exact residual mean: 0.00003198102058377117
positive exact residual reduction ratio: 0.8982656378486144
accepted backtracking step count: 1
accepted factor: 0.25
repaired checkpoint written: false
guardrail violation count: 0
passes public smoke gates: true
```

M1644 audited M1643 as a local exact-objective pass only and admitted a fixed
multi-scale, multi-seed no-checkpoint stress test.

M1645 designed that stress grid:

```text
perturb scales: [1e-4, 3e-4, 1e-3]
perturb seeds: [1645, 1646, 1647]
stress candidates: 9
projection mode: damped_backtracking
```

M1646 implemented and ran the grid. All nine controlled perturbations reduced
the positive exact residual and passed candidate public gates:

```text
stress candidate count: 9
measurable initial residual count: 9
residual reduced count: 9
candidate public pass count: 9
accepted backtracking candidate count: 9

min positive exact residual reduction ratio:    0.7070986860856349
median positive exact residual reduction ratio: 0.7420973915926545
max positive exact residual reduction ratio:    0.8632753818236488
```

M1646 guardrails remained clean:

```text
checkpoint artifact count: 0
base interpolation used for repair count: 0
diagnostic rows used as positive count: 0
donor_plus action used as loss target count: 0
training/PPO/promotion/private holdout/actor-input/level3 claim counts: 0
```

M1647 audited M1646 as a clean fixed-grid infrastructure pass and explicitly
kept checkpoint artifact generation, PPO-proposal repair, closed-loop
improvement, behavior retention, promotion, private-holdout evidence,
paper-level evidence, and level3 self-ID unsupported.

## Supported Claims

The branch supports:

```text
the contour-aware policy-target tensors can be used as exact projection targets;
the exact objective detects controlled policy-output drift;
Adam lr=1e-3 is too coarse for the small actor_mean perturbation scale;
damped full-batch backtracking repairs controlled actor_mean drift;
the damped repair rule is stable over the pre-registered 3x3 perturbation grid;
diagnostics remain zero-weight guardrails;
donor-plus actions remain excluded from loss targets;
no checkpoint artifact is needed to validate the local projection rule;
the branch is mature enough to stop local projection rolling and enter a new design branch.
```

## Falsified Or Rejected Claims

The branch falsifies or rejects:

```text
the original M1640 Adam projection recipe is adequate;
one local controlled perturbation is enough to justify checkpoint artifacts;
fixed-public-tensor exact-objective repair proves closed-loop behavior;
fixed-public-tensor exact-objective repair proves behavior retention;
fixed-public-tensor exact-objective repair is promotion evidence;
fixed-public-tensor exact-objective repair is paper-level evidence;
fixed-public-tensor exact-objective repair proves level3 self-identification;
another local stress implementation on the same public tensors is the highest-leverage next step.
```

No result falsifies the damped projection idea. The current limitation is scope:
the branch has only shown controlled public-tensor policy-output repair, not
repair of a real PPO/proposal delta.

## Failure Taxonomy Summary

Failure taxonomy by milestone:

```text
M1640: training_instability
M1641: none
M1642: none
M1643: none
M1644: none
M1645: none
M1646: none
M1647: none
```

M1640 used `training_instability` for optimizer-step instability even though no
environment training or PPO ran. The later damped/backtracking route resolved
that specific failure class for controlled actor_mean perturbations.

The important remaining risks are not resolved failures:

```text
controlled actor_mean perturbations are not PPO proposals;
public exact tensors can become an overfit target;
repairing action residuals does not prove closed-loop replay retention;
actor_mean-only repair may be insufficient for broader proposal deltas;
diagnostic guardrails are public controls rather than private validation.
```

## Public-Gate Overfit Risk

Public-gate overfit risk remains high:

```text
positive target count: 39
diagnostic guardrail count: 232
all tensors are public proof plumbing;
the stress grid is fixed and small;
the repaired objective restores known target actions rather than discovering new behavior;
the result has not run any replay, behavior, generalization, or private-holdout gate.
```

Mitigation:

```text
close the local projection branch now;
do not run another same-surface local projection implementation;
do not write checkpoint artifacts from M1646/M1647;
do not promote or run private holdout;
move only to design for PPO-proposal repair;
require any future proposal-repair implementation to be no-checkpoint first;
require exact-objective gates before any replay gates;
require replay/behavior/generalization gates before any promotion route.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Next branch:

```text
paper_route_ppo_proposal_projection_repair
```

Next task:

```text
m1649-paper-route-ppo-proposal-damped-projection-repair-design
```

M1649 should design how to apply the damped projection rule to a real proposal
delta rather than a synthetic actor_mean perturbation. The design should keep
PPO as a proposal source and exact objectives as pre-replay feasibility checks.

M1649 must remain design-only. It should not run PPO, repair a checkpoint,
write a checkpoint, evaluate closed-loop behavior, promote, use private
holdout, change actor inputs, or claim paper-level or level3 self-ID evidence.
