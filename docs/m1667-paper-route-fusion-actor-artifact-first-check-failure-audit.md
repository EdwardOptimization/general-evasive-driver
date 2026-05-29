# M1667 Paper-Route Fusion Actor Artifact First-Check Failure Audit

## Summary

M1667 audits the M1666 first-check replay failure before any repair, PPO,
training, promotion, or private-holdout route.

Decision:

```text
fusion_actor_artifact_first_check_failure_audit_route_to_branch_synthesis
```

M1666 is a clean negative result. The M1663 checkpoint artifact loads, its
checksum matches, and its P0 actor contract is intact. The first-check replay
failure is therefore not a lineage, contract, or metric artifact. It is a real
closed-loop behavior/proof retention failure.

The next step should be branch synthesis, not immediate repair. The branch has
now shown that fixed-public exact residual repair can produce a checkpoint
artifact, but that artifact can still destroy normal-history replay behavior.

## Audited Evidence

```text
runs/m1666_fusion_actor_artifact_replay_first_check/summary.json
runs/m1666_fusion_actor_artifact_replay_first_check/checkpoint_sanity.json
runs/m1666_fusion_actor_artifact_replay_first_check/first_check_gate_summary.csv
docs/m1666-paper-route-fusion-actor-artifact-replay-first-check.md
```

Stage 0 passed:

```text
checkpoint_sanity_pass: true
artifact_sha256_match: true
p0_actor_contract_pass: true
lineage_invalid_count: 0
contract_violation_count: 0
metric_artifact_count: 0
```

Stage 1 failed:

```text
m183_m170_first_check_pass: false
m267_m264_first_check_pass: false
first_check_pass: false
proof_washout_count: 2
behavior_regression_count: 2
```

## Failure Classification

Primary blocker:

```text
behavior_regression
```

The artifact fails normal-history replay:

```text
M183/M170 normal_success_delta: -1.0
M183/M170 normal_margin_mean_delta: -0.011979825763062477
M267/M264 normal_success_delta: -0.8823529411764706
M267/M264 normal_margin_mean_delta: -0.01067500028918613
```

Secondary observed failure:

```text
proof_washout
```

The success-drop proof count collapses because the normal branch no longer
succeeds:

```text
M183/M170 success_drop_count_delta: -17
M267/M264 success_drop_count_delta: -15
```

Important nuance:

```text
wrong_history_gap_retention_pass: true on both surfaces
```

So this is not primarily a wrong-history branch becoming safe. It is the repaired
artifact making the normal branch unsafe.

## Branch Implication

The sequence M1660-M1666 establishes:

```text
fusion_actor exact residual can be reduced;
the reduced-residual policy can be materialized as a valid checkpoint artifact;
checkpoint lineage and P0 actor contract can be kept clean;
but the artifact fails first closed-loop proof replay because normal behavior regresses.
```

This falsifies the stronger local claim:

```text
fixed-public exact residual repair alone is enough to produce a replay-worthy checkpoint artifact.
```

It does not falsify the broader research direction. It says the next objective
needs behavior/trajectory retention or a different projection contract before
another artifact route.

## Route Decision

Do not immediately design another repair. The next task should synthesize the
proposal-projection/artifact branch and decide whether to:

```text
pivot to behavior-retention-constrained repair;
pivot to replay-aware projection;
refresh sources before repair;
stop the current artifact route;
or promote a new branch with different evidence axis.
```

Admit:

```text
m1668-paper-route-proposal-projection-artifact-branch-synthesis
```

## Unsupported Claims

M1667 does not support:

```text
repair design;
PPO-proposal repair;
full-stack replay;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

Repair, PPO, and private holdout remain blocked until the synthesis milestone
chooses a route.
