# M1659 Paper-Route Proposal Projection Repair Branch Synthesis

## Summary

M1659 synthesizes the M1649-M1658 proposal-projection-repair branch before any
fusion_actor implementation, checkpoint artifact, replay gate, PPO, or
promotion.

Synthesis decision:

```text
continue
```

Route decision:

```text
admit exactly one no-checkpoint fusion_actor repair implementation
```

This synthesis does not run repair, train, run PPO, evaluate closed-loop
behavior, write a checkpoint, promote, use private holdout, change actor inputs,
or claim paper-level or level3 self-identification evidence.

## Evidence Summary

M1649 opened the branch by designing a real proposal-delta repair route, with
M1362 same-line interpolation candidates as the first no-checkpoint source
family.

M1650 implemented proposal-source preflight. It found:

```text
source candidate count: 10
branch-compatible candidate count: 10
larger proposal candidate count: 5
selected repair candidate count: 5
selected alphas: 0.2, 0.4, 0.6, 0.8, 1.0
checkpoint artifact count: 0
projection used count: 0
proposal repaired count: 0
```

M1651 audited the preflight as clean metadata only. M1652 then selected alpha
`0.2`, `0.4`, and `1.0` for a no-checkpoint actor_mean-only repair
implementation.

M1653 implemented and ran that selected-proposal actor_mean repair. The result
was a clean negative:

```text
selected_candidate_count: 3
measurable_initial_residual_count: 3
residual_reduced_count: 1
candidate_public_pass_count: 0
primary_alpha_0_2_pass: false
alpha_0_2_reduction_ratio: 0.0
alpha_0_4_reduction_ratio: 0.0
alpha_1_0_reduction_ratio: 0.07257319479554114
guardrail violation count: 0
```

M1654 audited that as actor_mean-only projection/scope insufficiency, not a
plumbing or role-contamination failure.

M1655 designed a scope-sensitivity preflight and identified a structural issue:
the M1640-M1653 exact-objective path was feature-frozen, so upstream parameter
scopes cannot be evaluated by merely setting more parameters trainable.

M1656 implemented the two-mode scope-sensitivity preflight. It passed:

```text
frozen_feature_upstream_grad_zero: true
differentiable_feature_scope_measurable_count: 5
primary_alpha_0_2_wider_scope_nonzero_grad_count: 4
primary_alpha_0_2_wider_scope_reduction_count: 4
model_restored_after_probe_count: 15
passes_public_smoke_gates: true
```

Primary alpha `0.2` differentiable-feature one-step reductions were:

```text
fusion_actor:           0.40519785496674926
context_fusion_actor:   0.4053135063761288
response_fusion_actor:  0.4005220459560401
full_policy_actor:      0.40066576536168946
```

M1657 audited the result and chose `fusion_actor` as the minimal justified wider
scope. M1658 designed a differentiable-feature `fusion_actor` repair route, but
workflow cadence required synthesis before implementation.

## Supported Claims

The branch supports:

```text
M1362 same-line proposal deltas can be used as public proposal-repair stressors;
actor_mean-only selected-proposal repair is insufficient for primary alpha 0.2;
the M1640-M1653 exact-objective repair path is structurally actor_mean-only because features are detached;
differentiable-feature wider scopes expose upstream gradient on the selected proposals;
the minimal wider scope, fusion_actor, is enough to reduce the primary alpha 0.2 residual in one temporary step;
a no-checkpoint fusion_actor repair implementation is justified as the next bounded objective-sanity test.
```

## Falsified Or Rejected Claims

The branch falsifies or rejects:

```text
actor_mean-only repair is enough for selected same-line proposal deltas;
alpha 1.0 partial actor_mean reduction should be treated as a candidate pass;
simply setting upstream parameters trainable is meaningful under a frozen-feature exact objective;
larger context/response/GRU scopes are justified before testing fusion_actor;
one-step scope sensitivity is full repair evidence;
fixed-public-tensor evidence is checkpoint, replay, PPO, promotion, private-holdout, paper-level, or level3 self-ID evidence.
```

No result rejects the proposal-repair branch itself. The evidence instead
narrows the next test to the minimal differentiable feature path.

## Failure Taxonomy Summary

Failure taxonomy by milestone:

```text
M1649: none
M1650: none
M1651: none
M1652: none
M1653: training_instability
M1654: training_instability
M1655: none
M1656: none
M1657: none
M1658: none
```

`training_instability` in M1653/M1654 means projection/scope insufficiency in
the repository taxonomy, not environment RL training or PPO.

Remaining risks:

```text
all evidence remains public fixed-tensor objective-sanity evidence;
one-step fusion_actor sensitivity may not survive multi-step repair;
multi-step exact repair may overfit selected public rows;
repairing exact residuals may not preserve closed-loop replay behavior;
no private holdout or paper-level comparison has been used.
```

## Public-Gate Overfit Risk

Public-gate overfit risk is high:

```text
the positive exact tensors are fixed and public;
the selected proposal set is only three same-line alpha candidates;
the current result is exact residual improvement, not closed-loop replay;
the next repair could optimize public proof rows without improving behavior.
```

Mitigation for the next step:

```text
allow exactly one no-checkpoint fusion_actor implementation;
require result audit before any checkpoint artifact or replay gate;
keep private holdout unused;
do not widen scope beyond fusion_actor inside the implementation;
do not promote from fixed-tensor objective-sanity metrics.
```

## Next Branch Decision

Decision:

```text
continue
```

Next task:

```text
m1660-paper-route-fusion-actor-proposal-repair-implementation
```

M1660 should run exactly the no-checkpoint differentiable-feature fusion_actor
repair designed in M1658. It must write metrics only and then route to result
audit whether it passes or fails.
