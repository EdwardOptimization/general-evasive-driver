# M1357 Paper-Route Bidirectional Replay Active-Set Design

## Summary

M1357 opens the bidirectional replay active-set branch after M1356 synthesis.

Decision:

```text
bidirectional_replay_active_set_design_admit_anchor_export
```

The next branch should not tune M1355's retention coefficient. M1355 already
showed the missing variable: protecting the normal branch alone can make
wrong-history branches safe. The next objective must explicitly protect both
branches.

## Problem Statement

M1355 produced this failure:

```text
normal_success_delta: 0.0
normal_margin_delta: +0.0010805264
success_drop_count_delta: -5
wrong-history safe rows: 6, 10, 13, 15, 16
```

So the retained update did not lose normal safety. It lost the intervention
proof:

```text
normal history still works;
wrong history now also works.
```

For self-identification proof surfaces, that is a failure. The proof requires
the current scene plus correct history to produce a safe branch while the same
scene plus wrong history remains behaviorally different enough to fail or keep
a margin gap.

## Design Principle

Use a bidirectional active-set objective:

```text
correct-history branch:
  retain or improve normal success and margin.

wrong-history branch:
  retain rejected/wrong-history action trajectory or enforce a separation floor.

source-history objective:
  improve materialized correct-vs-wrong preference without collapsing either
  branch.
```

This is not a claim that wrong history is deployed. Wrong history is an
intervention used to prove the policy's behavior depends on its history state.

## Existing Tooling

The branch can reuse existing tooling:

```text
normal/correct branch:
  terminal_margin_retention_surface.py
  already used by M1355 to export M1154 normal trajectories.

wrong/rejected branch:
  rejected_history_trajectory_anchor.py
  can export wrong-history action trajectories from the public boundary corpus.

update loss:
  materialized_source_history_replay_aware_retention_probe.py can be extended
  later to consume a combined trajectory anchor.
```

Because the anchor exporter already exists, M1358 should export bidirectional
anchor artifacts before another update. Do not jump directly to training.

## Active Rows

Primary wrong-history active rows come from M1355 M267/M264 failure:

```text
6, 10, 13, 15, 16
```

These are rows where M1154 had success drop and M1355 did not.

Correct-history active rows remain the M1355 retention surface:

```text
M183/M170 hard rows:
1, 4, 12, 14, 16

M183/M170 expanded rows:
1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16

M267/M264 lower-weight rows:
rows selected by normal margin threshold from M1355 retention export
```

M1358 should start with the M267/M264 wrong-history rows because those are the
actual M1355 proof-washout rows. M183/M170 rejected anchors can be added later
only if the first branch-asymmetric export is structurally valid.

## Proposed Objective For Later Probe

The later no-PPO probe should use:

```text
L = L_source
  + lambda_correct * L_correct_trajectory_anchor
  + lambda_wrong * L_wrong_trajectory_anchor
  + lambda_gap * L_normal_wrong_separation_floor
  + lambda_trust * L_param_base
```

Where:

```text
L_source:
  M1336/M1339/M1342 materialized source-history pair-group objective.

L_correct_trajectory_anchor:
  normal/correct-history M1154 trajectories on replay-active rows.

L_wrong_trajectory_anchor:
  wrong-history M1154 rejected trajectories on rows 6,10,13,15,16.

L_normal_wrong_separation_floor:
  optional action-space separation floor so wrong branch cannot collapse onto
  the normal branch even if action anchoring is weak.

L_param_base:
  parameter trust region to M1154.
```

The first implementation should not include PPO or private holdout. It should
remain a no-PPO public proof probe.

## M1358 Export Design

M1358 should run an artifact-only export:

```text
base correct anchor:
  runs/m1355_materialized_source_history_replay_aware_retention_probe/
    retention_surface/retention_trajectory_anchor.npz

wrong-history corpus:
  runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv

required wrong-history row ids:
  6, 10, 13, 15, 16

exporter:
  python -m autodrift.rejected_history_trajectory_anchor
```

Expected outputs:

```text
rejected_trajectory_anchor.npz
rejected_trajectory_anchor.csv
combined_recovery_rejected_anchor.npz
summary.json
```

The combined anchor should include both the existing correct-history retention
anchor and repeated wrong-history rejected branch rows.

M1358 should not update actor weights. It should only prove the branch-asymmetric
anchor artifacts can be built and loaded.

## Admission Criteria For A Later Probe

Only after M1358 passes should a later probe run a no-PPO update.

That probe must require:

```text
actor input contract unchanged
forbidden_parameter_mutation_detected=false
log_std_l2=0.0
exact metrics improve vs M1154
M267/M264 success-drop count retained
M183/M170 run only if M267/M264 passes
no PPO
no private holdout
no promotion
```

If the update still makes wrong-history rows successful, classify it as
`proof_washout` and synthesize rather than tuning coefficients in-place.

## Guardrails

M1357 performs no training, PPO, actor update, replay run, private holdout,
promotion, threshold relaxation, actor-input expansion, high-fidelity claim,
paper-level claim, or closed-loop self-identification claim.

## Next

```text
m1358-paper-route-bidirectional-active-set-anchor-export
```
