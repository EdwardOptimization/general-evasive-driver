# M274 Terminal-Margin Retention Design

M274 designs the retention layer required after M273 showed that the promoted
M272 checkpoint is limited by a terminal-margin cliff on M183/M170 row16.

No PPO, actor update, promotion, or actor-input change was performed.

## Problem

M271-style objectives are steerable: the M270 exact and sampled losses improve
as interpolation moves toward the M271 actor update. The failure is closed-loop
retention. M183/M170 row16 crosses from success to collision between:

```text
alpha = 0.01025  normal_margin = +0.000000636
alpha = 0.01050  normal_margin = -0.000000087
```

The first-action L2 change across that boundary is only:

```text
0.000001841
```

This means a first-action or snippet-only anchor is not enough. The row needs a
terminal-margin-aware retention rule.

## Existing Tools

Already available:

- `boundary_outcome_replay_gate`: exact closed-loop row replay and pass/fail
  comparison;
- `checkpoint_interpolation`: post-update trust-region interpolation;
- `outcome_intervention_optimize`: source/snippet outcome objective;
- `trajectory_action_anchor_loss`: differentiable action-sequence anchor;
- `M270` source-balanced objective corpus;
- `M272` selected public-gate base.

Missing:

- a current-family fragile-row registry;
- a way to export current fragile closed-loop trajectories into the existing
  `TrajectoryActionAnchor` NPZ format;
- a single terminal-margin gate matrix that runs before any promotion or PPO;
- an explicit rule for rows with tiny positive terminal margin.

## Design

M274 chooses a two-layer retention design.

### Layer 1: Hard Terminal-Margin Gate

This is non-differentiable and uses real simulator replay.

For each registered fragile row, a candidate must satisfy:

```text
normal_success == true
success_drop retained
normal_margin > 0
normal_margin >= baseline_normal_margin - allowed_regression
```

For near-zero rows, `allowed_regression` must be tightened. For M183/M170 row16:

```text
baseline = m272b_a0_01025
baseline_normal_margin = 0.000000636
allowed_regression = 0.0000005
hard_floor = 0
```

The hard gate is lexicographic. If it fails, the candidate is rejected before
behavior, protected-key, or promotion checks.

### Layer 2: Differentiable Trajectory Proxy

Terminal margin is not currently differentiable through the simulator. The
training-time proxy should use the existing trajectory-action-anchor mechanism,
but with a refreshed fragile-row export:

```text
observation
hidden
reference_action
source_index
step_index
weight
```

Rows receive inverse-margin weights:

```text
weight = source_weight * clamp(1 / (normal_margin + eps), max_weight)
```

M183/M170 row16 must be a hard included source regardless of weighting.

The anchor should export two variants:

1. `retention_anchor`: current M272 normal trajectory, used to avoid further
   margin loss.
2. `recovery_anchor`: safer source trajectory when available, for row16 this is
   the M170 source trajectory whose normal margin is much larger.

M275 should export both and validate their shapes. A later actor update can
start with retention-only; recovery anchor should be tried only if retention
alone prevents all useful movement.

## First Guarded Update Recipe

Do not run it in M274. The first admissible future update should be:

```text
init = m272b_a0_01025
objective = M270 source-balanced outcome/snippet objective
anchors =
  M270 snippet action anchor
  M275 terminal-margin trajectory retention anchor
train_scope = actor_coupling
steps = 5 to 10
learning_rate <= 5e-5
post_update = interpolation line search back to m272b_a0_01025
hard gates =
  M183/M170 row16 terminal-margin gate first
  full six replay surfaces
  protected key diagnostic
  behavior seeds
```

If the row16 terminal-margin gate fails at every alpha that improves the
objective, the update direction is rejected and the next repair must be
margin-recovery, not PPO.

## M275 Implementation Scope

M275 should implement or export:

```text
runs/m275_terminal_margin_retention_surface/fragile_rows.csv
runs/m275_terminal_margin_retention_surface/terminal_margin_registry.csv
runs/m275_terminal_margin_retention_surface/retention_trajectory_anchor.npz
runs/m275_terminal_margin_retention_surface/recovery_trajectory_anchor.npz
runs/m275_terminal_margin_retention_surface/summary.json
```

Minimum required fragile rows:

- M183/M170 row16;
- any M183/M168, M183/M170, M193/M189, M212/M204, M223/M219, or M267/M264 row
  under the current base with `0 < normal_margin <= 0.001`.

M275 is still not a training milestone. It should validate the export and gate
semantics first.

## Decision

M274 completes the design.

Decision:

```text
implement_terminal_margin_retention_surface_export
```

Next step:

```text
m275-terminal-margin-retention-surface-export
```

M275 should build the fragile-row registry and trajectory-anchor exports before
any new actor update or PPO continuation.
