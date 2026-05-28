# M1354 Paper-Route Materialized Source-History Replay-Aware Retention Design

## Summary

M1354 designs the next no-PPO update after M1352/M1353.

Decision:

```text
materialized_source_history_replay_aware_retention_design_admit_probe
```

The key result from M1352 is not that `alpha=0.005` should become a new base.
The key result is that the raw M1346 source-history objective direction crossed
active closed-loop replay constraints. A line search found the boundary. The
next update should include those active replay constraints directly.

## Control Interpretation

M1346 optimized a fixed source-history objective:

```text
improve correct-history versus wrong-history action preference
improve pair-group minimum joint margin
```

But it did not include closed-loop normal-branch replay retention. M1349 showed
that raw M1346 collapses M267/M264 normal success on `17/17` rows. M1352 then
showed that the same direction is usable only in a tiny region:

```text
M267/M264 passes through alpha 0.02
M183/M170 passes only at alpha 0.005
```

That is an active-set update problem:

```text
maximize source-history objective progress
subject to replay retention constraints remaining feasible
```

So M1355 should stop relying on post-hoc interpolation and include replay-aware
retention in the update loss.

## Base And Candidate Policy

The official base remains:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

The M1352 `alpha=0.005` checkpoint is diagnostic only:

```text
runs/m1352_materialized_source_history_interpolation_preflight/checkpoints/alpha_0_005.pt
```

It may be used as a comparison point, but M1355 should start the update from
M1154 unless the implementation explicitly records why a different start is
needed.

## Active Replay Rows

M1352 identifies two kinds of active replay rows.

M183/M170 is the hard surface. It first fails at `alpha=0.01`:

```text
critical row_ids at alpha 0.01:
1, 4, 12, 14, 16
```

At `alpha=0.02`, M183/M170 failure expands to:

```text
1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16
```

M267/M264 is the softer surface. It first fails at `alpha=0.05`:

```text
0, 1, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16
```

The base M1154 margins show why M183/M170 is the hard constraint:

```text
M183/M170 base normal_margin_min: 0.0009344382
M183/M170 base normal_margin_mean: 0.0025228923
M267/M264 base normal_margin_min: 0.0038957677
M267/M264 base normal_margin_mean: 0.0071805653
```

M1355 should therefore weight M183/M170 harder than M267/M264.

## Proposed M1355 Objective

Use the same trainable scope as M1346:

```text
response_context_fusion.0.weight
response_context_fusion.0.bias
actor_mean.weight
actor_mean.bias
```

Keep all other actor parameters frozen, including `log_std`.

The loss should combine:

```text
L_source:
  M1336/M1339/M1342 materialized source-history row and pair-group objective.

L_active_retention:
  trajectory/action retention on M1154 normal-history behavior for active replay
  rows from M183/M170 and M267/M264.

L_trust:
  parameter trust region to M1154, optionally with distance-to-M1346 direction
  only as a secondary diagnostic.
```

Suggested first form:

```text
L = L_source
  + lambda_m183 * L_retention_m183
  + lambda_m267 * L_retention_m267
  + lambda_trust * L_param_base
```

Initial weighting:

```text
lambda_m183 > lambda_m267
lambda_m183 hard rows: row_ids 1, 4, 12, 14, 16
lambda_m183 expanded rows: row_ids 3, 5, 6, 7, 8, 9, 10, 11, 13
lambda_m267 rows: lower weight unless M267/M264 fails in the probe
```

If the existing trajectory-anchor loader is used, the first implementation can
export M1154 normal trajectories from the M1352 replay surfaces and use
`exact_trajectory_action_anchor_loss`. A small action radius is acceptable, but
the design should start conservative: M183/M170 near-boundary rows should not be
allowed to drift enough to lose normal success.

## Implementation Shape

M1355 should be a single no-PPO probe:

```text
1. Build replay active-set registry from M1352 replay rows.
2. Export or load base-normal retention trajectories for selected active rows.
3. Run a bounded M1346-style source-history update with retention terms.
4. Verify mutation scope and actor input contract.
5. Evaluate exact source-history row/group metrics.
6. Run M267/M264 replay.
7. Run M183/M170 replay only if M267/M264 passes.
8. Stop and write summary; do not promote.
```

The probe should compare against both:

```text
M1154 base
M1352 alpha 0.005 diagnostic checkpoint
```

The useful target is:

```text
more exact progress than alpha 0.005
while retaining M267/M264 and M183/M170 replay surfaces
```

If it cannot beat alpha `0.005` while passing replay, that is a useful negative
result and should route to synthesis rather than more local tuning.

## Acceptance Criteria For M1355

Required structural checks:

```text
actor input contract unchanged
forbidden_parameter_mutation_detected=false
log_std_l2=0.0
training is no-PPO only
no private holdout
no promotion
no threshold relaxation
```

Required exact checks:

```text
combined_loss_mean improves vs M1154
group_min_joint_margin_mean improves vs M1154
eval_fold_4 group_min_joint_margin does not regress vs M1154
exact progress is compared against alpha 0.005
```

Required replay checks:

```text
M267/M264 passes the same retention thresholds as M1352
M183/M170 passes the same retention thresholds as M1352
```

If both replay surfaces pass and exact progress clearly exceeds alpha `0.005`,
M1355 should still not promote. It should route to branch synthesis because the
current branch is at the cadence boundary.

## Rejected Alternatives

Rejected:

```text
direct PPO from alpha 0.005
```

Reason: alpha `0.005` is not a promoted base and the branch has not shown stable
replay-aware objective progress.

Rejected:

```text
direct full public replay of alpha 0.005
```

Reason: it would answer whether a tiny diagnostic point survives more gates, but
it would not solve the update design problem revealed by M1346/M1352.

Rejected:

```text
relaxing replay thresholds
```

Reason: the goal is preserving self-ID proof surfaces, not making the gate pass.

## Guardrails

M1354 performs no training, PPO, actor update, replay run, private holdout,
promotion, threshold relaxation, actor-input expansion, high-fidelity claim,
paper-level claim, or closed-loop self-identification claim.

## Next

```text
m1355-paper-route-materialized-source-history-replay-aware-retention-probe
```
