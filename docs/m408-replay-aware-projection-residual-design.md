# M408 Replay-Aware Projection Residual Design

M408 designs the next repair path after M406/M407 showed that exact M297/M270
and old-key surrogate feasibility are not enough to preserve closed-loop replay
proof. This milestone does not train, promote, lower thresholds, or change actor
inputs.

## Problem

M406 produced an exact-feasible projection that also moved toward the M398
recovery target, but closed-loop replay failed:

```text
M267/M264 success drops: 1 / 17
old-key accepted regressions: 7 / 40
```

M407 classified the failure:

```text
M267/M264: 16 / 17 rows become wrong-history successes
old-key: 6 wrong-history-safe regressions + 1 normal-branch failure
```

This means the exact corpora are a weak proxy for continuation behavior in this
region. The failed candidate changes actions only modestly, but those changes
are enough to make wrong-history rollouts survive.

## Design Principles

The next residual must obey these constraints:

```text
1. Actor inputs stay P0 human-view no-wheel.
2. Replay labels and terminal outcomes are training-only residual data.
3. Closed-loop replay gates remain the authority.
4. Exact M297/M270/old-key no-regression remains lexicographic feasibility.
5. Replay-aware terms are used only to propose candidates, not to replace gates.
```

This is not a rule controller and does not add oracle information at runtime.
It is a training-time projection constraint built from public proof rows.

## Residual Shape

The preferred residual is a branch-specific trajectory action anchor:

```text
L_replay_anchor =
  weighted MSE(pi(obs_t, hidden_branch_t), reference_action_t)
```

For M407 rows:

| Row family | Branch | Reference |
| --- | --- | --- |
| M267/M264 wrong-history washout rows | rejected/wrong-history hidden | M400 wrong-history collision-side trajectory |
| old-key wrong-history-safe rows | rejected/wrong-history hidden | M400 wrong-history boundary trajectory |
| old-key normal-branch failure row | normal/preferred hidden | local normal recovery target or M400 normal successful trajectory |

The rejected/wrong-history anchor is important because M407 showed the failure
is mostly not normal driving. The candidate made wrong-history branches safer;
the next residual must preserve the counterfactual branch behavior while still
allowing normal/recovery branch improvements.

## Implementation Path

Use existing assets where possible:

```text
src/autodrift/rejected_history_trajectory_anchor.py
src/autodrift/intervention_objectives.py::load_trajectory_action_anchor
src/autodrift/intervention_objectives.py::trajectory_action_anchor_loss
```

M409 should add two pieces:

1. Export a replay-failure trajectory anchor from M407 rows.

   For M267/M264, reuse the existing rejected-history trajectory anchor export
   with the M407 failed row ids. For old-key, add the minimal exporter needed to
   replay the compact old-key failed rows and save branch-specific observation,
   hidden, and reference action sequences from the M400 base.

2. Add optional trajectory-anchor terms to `exact_post_ppo_repair`.

   The projection loss should become:

```text
hard feasibility:
  hinge(exact_M297 - base_M297)
  hinge(exact_M270 - base_M270)
  hinge(old_key_surrogate - base_old_key)

secondary residuals:
  old_key_recovery
  current_family_conflict
  replay_failure_trajectory_anchor
  action_anchor
  param trust region
```

The trajectory anchor should not be part of the exact lexicographic pass. It is
a proposal-shaping residual. A candidate still must pass M267/M264 and old-key
closed-loop replay.

## Initial M409 Probe

M409 should implement and smoke-test the infrastructure only:

```text
export M407 replay-failure trajectory anchor
wire --replay-trajectory-anchor-npz into exact_post_ppo_repair
verify no-update exact repair loads the anchor
run focused tests
do not train PPO
do not promote
```

If implementation passes, M410 can run the no-PPO projection probe:

```text
base: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
raw:  runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt
required gates:
  exact M297/M270/old-key no-regression
  distance to M398 recovery target improves
  M267/M264 first replay 17 / 17
  cumulative old-key compact replay passes
```

## Why Not Another Scalar Sweep

M403 already showed recovery scalar sweeps split into two bad regimes:

```text
exact-safe but no useful recovery movement
recovery movement but exact/replay failure
```

M406/M407 add the missing diagnosis: exact-feasible movement can still wash out
wrong-history closed-loop behavior. A replay-aware trajectory residual is the
smallest next mechanism that directly targets the observed failure without
changing the actor contract.

## Decision

Admit implementation:

```text
m409-replay-failure-trajectory-anchor-implementation
```
