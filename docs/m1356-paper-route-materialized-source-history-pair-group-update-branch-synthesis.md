# M1356 Paper-Route Materialized Source-History Pair-Group Update Branch Synthesis

## Summary

M1356 synthesizes the M1346-M1355 bounded pair-group update branch.

Synthesis decision:

```text
pivot
```

Closed branch:

```text
paper_route_materialized_source_history_pair_group_update_implementation
```

Opened branch:

```text
paper_route_bidirectional_replay_active_set_retention
```

The branch proved that materialized source-history objectives have a strong
trainable signal, but also proved that fixed source-history progress is not
enough. The update must treat correct-history success and wrong-history rejected
behavior as separate active branches.

## Evidence Summary

M1346 ran the first bounded no-PPO pair-group update from M1154:

```text
combined_loss_mean: 6.8847534022 -> 1.9998926339
group_min_joint_margin_mean: -6.8026667906 -> -1.1251848645
eval_fold_4 group_min: -6.4443958161 -> -1.2625397266
all-rows-both-directional groups: 0 -> 27
both-negative groups: 4 -> 26
```

M1349 rejected raw M1346 on replay:

```text
M267/M264 normal success: 1.0 -> 0.0
success-drop count: 17 -> 0
normal margin mean delta: -0.1065894892
```

M1352 line-searched the M1346 direction:

```text
alpha 0.005: M267/M264 pass, M183/M170 pass
alpha 0.01: M267/M264 pass, M183/M170 fail
alpha 0.02: M267/M264 pass, M183/M170 fail
alpha >= 0.05: M267/M264 fail
```

M1352 showed a tiny replay-safe region exists, but the exact lift at
`alpha=0.005` is weak:

```text
combined_loss_delta: -0.0317072824
group_min_joint_margin_delta: +0.0322478571
eval_fold_delta: +0.0299366837
all-rows-both-directional groups: 0
```

M1355 tried replay-aware normal-branch retention:

```text
retention fragile rows: 29
retention trajectory rows: 1409
combined_loss_delta: -4.6874377849
group_min_joint_margin_delta: +5.2968078983
eval_fold_delta: +4.8873970864
M267/M264 normal_success_delta: 0.0
M267/M264 normal_margin_delta: +0.0010805264
M267/M264 success_drop_count_delta: -5
```

M1355 preserves normal success but makes wrong-history rollouts successful on
rows:

```text
6, 10, 13, 15, 16
```

M183/M170 was skipped because M267/M264 failed first.

## Supported Claims

Supported:

```text
The allowed `response_context_fusion + actor_mean` scope can strongly optimize
the materialized source-history objective without mutating forbidden parameters.
```

Supported:

```text
Raw source-history improvement can destroy closed-loop replay proof by colliding
the normal branch.
```

Supported:

```text
Post-hoc interpolation finds only a tiny usable region and does not create a
meaningful new policy candidate.
```

Supported:

```text
Normal-branch trajectory retention fixes the normal collision failure mode but
does not protect self-ID proof, because it can make wrong-history branches safe.
```

Supported:

```text
The next objective must be bidirectional or branch-asymmetric: correct history
should remain safe, while wrong/rejected history must remain behaviorally
distinct enough to preserve the public proof surface.
```

## Falsified Claims

Falsified:

```text
The fixed pair-group source-history objective alone is replay-safe.
```

Falsified:

```text
Pure line search is enough to recover a useful policy candidate from M1346.
```

Falsified:

```text
Normal-branch replay retention alone is sufficient.
```

Unsupported:

```text
Any M1346/M1352/M1355 checkpoint is promotable.
```

Unsupported:

```text
This branch proves strong closed-loop self-identification.
```

## Failure Taxonomy Summary

Observed failures:

```text
proof_washout:
  M1349 raw M1346 makes normal branch collide.
  M1355 retained update makes wrong-history branches successful.

objective_overfit:
  M1346/M1355 fixed exact metrics improve much more than replay proof.

public_gate_overfit_risk:
  high, because all checks are fixed public source/replay surfaces.
```

No contract violation occurred:

```text
actor input contract unchanged
log_std_l2: 0.0
forbidden_parameter_mutation_detected: false
private_holdout_used: false
promoted: false
ppo_used: false
```

## Public Gate Overfit Risk

Risk remains high. The branch is entirely public-gate and fixed-corpus work.
That is appropriate for mechanism debugging, but not paper-level validation.
The next branch may still use public proof surfaces, but it must not promote or
claim driver improvement until later fresh/generalization gates are added.

## Next Branch Decision

Pivot to:

```text
paper_route_bidirectional_replay_active_set_retention
```

Next milestone:

```text
m1357-paper-route-bidirectional-replay-active-set-design
```

The new branch should design an objective that explicitly separates:

```text
correct-history branch:
  preserve normal success and margin.

wrong-history branch:
  preserve rejected/wrong-history distinct behavior, margin gap, or failure on
  intervention-only replay rows.

source-history objective:
  improve materialized correct-vs-wrong action preference without collapsing
  either branch.
```

This should be framed as a constrained active-set problem, not more coefficient
tuning:

```text
maximize source-history objective progress
subject to correct-history branch constraints
and wrong-history branch constraints
```

## Guardrails

M1356 performs no training, PPO, actor update, replay run, private holdout,
promotion, threshold relaxation, actor-input expansion, high-fidelity claim,
paper-level claim, or closed-loop self-identification claim.
