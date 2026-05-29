# M1668 Paper-Route Proposal Projection Artifact Branch Synthesis

## Summary

M1668 synthesizes the M1660-M1667 proposal-projection/artifact branch after the
M1663 exact-objective artifact failed first public replay checks.

Synthesis decision:

```text
promote_to_next_branch
```

Route decision:

```text
stop_exact_residual_artifact_route_promote_to_controller_family_current_state_audit
```

This synthesis does not run repair, replay, PPO, training, promotion, private
holdout, actor-input changes, or level3 self-identification claims.

## Evidence Summary

M1659 admitted exactly one no-checkpoint `fusion_actor` proposal repair
implementation after actor-mean-only repair failed and differentiable
`fusion_actor` scope sensitivity succeeded.

M1660 implemented that no-checkpoint repair and passed the public
objective-sanity gate:

```text
selected_candidate_count: 3
candidate_public_pass_count: 3
primary_alpha_0_2_pass: true
alpha_0_2_reduction_ratio: 0.40519785496674926
alpha_0_4_reduction_ratio: 0.3681913379827455
alpha_1_0_reduction_ratio: 0.8524941253365563
checkpoint_artifact_count: 0
```

M1661 audited that as a clean fixed-public-tensor objective-sanity positive.
M1662 designed a primary-only checkpoint artifact route, explicitly deferring
alpha `0.4` and alpha `1.0`.

M1663 materialized exactly one alpha `0.2` checkpoint artifact:

```text
artifact: runs/m1663_fusion_actor_checkpoint_artifact/checkpoints/alpha_0_2_fusion_actor_repaired.pt
artifact_sha256: c7829fc0596bd6658440fd343282a4cbb2907a37b6b30424698c2e29d0b8c191
selected_alpha: 0.2
checkpoint_artifact_count: 1
positive_exact_residual_reduction_ratio: 0.40519785496674926
```

M1664 audited the artifact as objective-sanity only. M1665 designed staged
public replay checks instead of running full-stack replay or promotion.

M1666 ran the first checks:

```text
checkpoint_sanity_pass: true
artifact_sha256_match: true
p0_actor_contract_pass: true
m183_m170_first_check_pass: false
m267_m264_first_check_pass: false
first_check_pass: false
```

The first-check failure was strong:

```text
M183/M170 normal_success_delta: -1.0
M183/M170 success_drop_count_delta: -17
M267/M264 normal_success_delta: -0.8823529411764706
M267/M264 success_drop_count_delta: -15
```

M1667 audited that as a clean negative:

```text
primary_blocker: behavior_regression
secondary_blocker: proof_washout
lineage_invalid_count: 0
contract_violation_count: 0
metric_artifact_count: 0
```

## Supported Claims

This branch supports:

```text
same-line proposal deltas can be used as public exact-objective stressors;
actor_mean-only repair is insufficient for primary alpha 0.2;
differentiable fusion_actor scope can reduce selected proposal exact residuals;
the alpha 0.2 fusion_actor repair can be materialized with clean lineage and P0 actor contract;
the materialized artifact can be evaluated by public replay gates;
first-check replay failure is a real closed-loop regression, not a lineage or contract artifact.
```

## Falsified Claims

This branch falsifies or rejects:

```text
fixed-public exact residual repair alone is enough to produce a replay-worthy checkpoint;
objective-sanity checkpoint artifacts should proceed directly to full-stack replay, PPO, or promotion;
wrong-history residual repair is sufficient if it ignores normal-history closed-loop behavior;
another immediate exact-residual-only repair on the same public artifact route is the highest-leverage next step.
```

The broader General Evasive Driver objective is not falsified. The result says
that this exact-residual-only artifact route is not enough.

## Failure Taxonomy Summary

Observed branch failures:

```text
M1653/M1654: training_instability / scope insufficiency for actor_mean-only repair
M1666/M1667: behavior_regression primary, proof_washout secondary
```

Important non-failures:

```text
lineage_invalid: 0
contract_violation: 0
metric_artifact: 0
private_holdout_contamination: 0
```

The final failure mode is clear: the artifact preserves the formal artifact and
input contract, but destroys normal-history replay behavior.

## Public-Gate Overfit Risk

Public-gate overfit risk is high:

```text
exact target tensors are fixed and public;
selected proposal candidates come from one same-line family;
the positive repair objective did not include closed-loop normal-retention;
first replay checks used public proof rows and immediately found regression;
continuing to repair the same artifact route risks becoming a fixed-row gate-passing loop.
```

M1668 should therefore not admit a direct repair implementation. A later repair
route would need a new branch with behavior/trajectory retention as a first-class
constraint and must justify why it is not just overfitting public replay rows.

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Close the current exact-residual artifact route and promote to:

```text
paper_route_controller_family_current_state_audit
```

The next milestone should audit the current L0/L1/L2/L3 go/no-go evidence and
decide which paper-route experiment is actually missing now. It should reconcile:

```text
M1205 finite-window-vs-GRU synthesis;
M1492 self-ID go/no-go matrix design;
M1498 standard profile three-seed negative/conditional audit;
M1499-M1667 decisive-history and exact-artifact evidence;
the updated long-term goal that treats GRU belief as a hypothesis, not an assumption.
```

Next task:

```text
m1669-paper-route-controller-family-current-state-audit
```

M1669 should not train or run replay. It should produce a current-state evidence
map and a concrete next experiment route for the paper objective.
