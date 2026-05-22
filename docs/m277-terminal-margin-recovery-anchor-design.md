# M277 Terminal-Margin Recovery Anchor Design

M277 designs the next repair after M276 showed that retention-only trajectory
anchoring does not recover terminal-margin slack.

No PPO, actor update, promotion, or actor-input change was performed.

## Failure Mechanism

M276 improved the M270 objective but failed M183/M170 row16:

```text
raw exact loss:     0.681376 -> 0.676400
raw sampled loss:   0.681592 -> 0.676587
row16 margin:       +0.000000636 -> -0.002258
```

Interpolation from M272 toward M276 found only a tiny safe range:

```text
alpha 0.0002: row16 margin = +0.000000170
alpha 0.0003: row16 margin = -0.000000022
```

The M275 retention anchor protects the current trajectory, but the current
trajectory is already almost unsafe. It prevents neither terminal-margin loss
under a real update nor creates useful new slack.

## Design Constraint

Do not import old checkpoint hidden states.

For example, M170 has a safer row16 terminal margin, but its recurrent hidden
state is not a valid input to the current M272 actor. A recovery anchor must
use:

```text
current M272 observation
current M272 recurrent hidden
safer reference action target
```

It must not use:

```text
old checkpoint hidden as current actor input
hidden params
mu / tire / slip / oracle labels
planner/reference shortcuts
```

## Recovery Anchor Contract

M277 selects a current-hidden local-action recovery design.

For each fragile row:

1. Reconstruct the current-base snapshot under `m272b_a0_01025`.
2. Record the current observation and current hidden before action.
3. Evaluate local first-action override candidates in the simulator.
4. Keep only overrides that improve terminal margin while preserving success.
5. Export the best override as `reference_action` using the current hidden.

This keeps the anchor deployable:

```text
observation = current human-view observation
hidden = current M272 hidden
reference_action = locally recovered safer action
```

The output can still use the existing `TrajectoryActionAnchor` format, but M278
should start with first-step recovery anchors before attempting multi-step
prefix anchors.

## Candidate Action Set

The first local grid should stay small and interpretable:

```text
steer_delta in {-0.01, 0, +0.01}
brake_delta in {-0.03, -0.015, 0, +0.015}
throttle_delta in {-0.02, 0}
```

Actions are clipped to the actor action range. For row16, the source evidence
suggests that releasing brake worsens terminal margin, so brake-increasing
candidates should be checked first.

M278 should also optionally include source-policy action vectors as candidate
actions, but only as action vectors evaluated under current snapshots. It must
not transfer source hidden states.

## Selection Rule

For each fragile row, the selected recovery action must satisfy:

```text
normal_success == true
terminal_margin > current_margin + min_margin_improvement
terminal_margin >= required_margin_floor
action_l2 <= max_action_l2
```

Recommended first thresholds:

```text
min_margin_improvement = 0.00005
max_action_l2 = 0.05
```

If no action improves a row, M278 should mark it as unrecovered instead of
fabricating a target.

## Export Artifacts

M278 should export:

```text
runs/m278_terminal_margin_recovery_anchor_probe/recovery_candidates.csv
runs/m278_terminal_margin_recovery_anchor_probe/recovery_anchor.npz
runs/m278_terminal_margin_recovery_anchor_probe/recovery_anchor.csv
runs/m278_terminal_margin_recovery_anchor_probe/unrecovered_rows.csv
runs/m278_terminal_margin_recovery_anchor_probe/summary.json
```

The NPZ should load through `load_trajectory_action_anchor`.

## Next Update Rule

Only after M278 proves at least row16 has a valid recovery action should a new
actor update be admitted. The update should use:

```text
M270 source-balanced objective
M275 retention trajectory anchor
M278 recovery action anchor
row16 terminal-margin hard gate first
```

PPO remains blocked.

## Decision

M277 completes the design.

Decision:

```text
implement_current_hidden_recovery_anchor_probe
```

Next step:

```text
m278-current-hidden-recovery-anchor-probe
```

M278 should implement the local-action recovery probe and export a validated
current-hidden recovery anchor before any further actor update.
