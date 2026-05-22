# M278 Current-Hidden Recovery Anchor Probe

M278 implements and runs a current-hidden local-action recovery probe for the
fragile terminal-margin rows exported in M275.

No PPO, actor update, promotion, or actor-input change was performed.

## Setup

Current base checkpoint:

```text
runs/m272_m264_to_m271_interpolation_boundary/checkpoints/alpha_0_01025.pt
```

Fragile-row registry:

```text
runs/m275_terminal_margin_retention_surface/terminal_margin_registry.csv
```

Environment:

```text
configs/m121_human_view_zero_obstacle_relvel.json
```

The probe reconstructs each fragile row under the current M272 actor, keeps the
current human-view observation and current recurrent hidden state, and evaluates
only first-action overrides in simulation.

## Implementation

Added:

```text
src/autodrift/terminal_margin_recovery_anchor.py
tests/test_terminal_margin_recovery_anchor.py
```

The exported anchor uses the existing `TrajectoryActionAnchor` format:

```text
observation = current M272 human-view observation
hidden = current M272 recurrent hidden
reference_action = simulator-selected safer first action
```

No hidden state from an older checkpoint is imported.

## Candidate Grid

The probe used the M277-registered grid:

```text
steer_delta = {-0.01, 0, +0.01}
brake_delta = {-0.03, -0.015, 0, +0.015}
throttle_delta = {-0.02, 0}
```

Selection thresholds:

```text
min_margin_improvement = 0.00005
max_action_l2 = 0.05
max_continuation_steps = 60
```

## Artifacts

Run directory:

```text
runs/m278_terminal_margin_recovery_anchor_probe
```

Artifacts:

```text
runs/m278_terminal_margin_recovery_anchor_probe/recovery_candidates.csv
runs/m278_terminal_margin_recovery_anchor_probe/recovery_anchor.csv
runs/m278_terminal_margin_recovery_anchor_probe/recovery_anchor.npz
runs/m278_terminal_margin_recovery_anchor_probe/unrecovered_rows.csv
runs/m278_terminal_margin_recovery_anchor_probe/summary.json
```

Summary:

| Metric | Value |
| --- | ---: |
| rows probed | 30 |
| candidate rollouts | 720 |
| accepted candidates | 360 |
| recovered rows | 30 |
| unrecovered rows | 0 |
| row16 probed | true |
| row16 recovered | true |
| recovered margin improvement min | 0.000400442 |
| recovered margin improvement mean | 0.000490056 |
| recovered margin improvement max | 0.000562197 |

Surface coverage:

| Surface | Recovered rows |
| --- | ---: |
| M183/M168 | 13 |
| M183/M170 | 14 |
| M193/M189 | 3 |

## Row16 Result

M183/M170 row16 was the first hard target because M276 failed there.

| Field | Value |
| --- | ---: |
| baseline margin | 0.000000636 |
| recovered margin | 0.000562819 |
| margin improvement | 0.000562183 |
| required margin floor | 0.000000136 |
| action L2 | 0.026925817 |
| base steer | 0.719243 |
| base throttle | -0.222729 |
| base brake | -0.014093 |
| reference steer | 0.709243 |
| reference throttle | -0.242729 |
| reference brake | 0.000907 |

The selected row16 recovery action stays inside the local trust region and
creates meaningful terminal-margin slack instead of preserving the near-zero
M272 action.

## Anchor Validation

The recovery NPZ loads through the existing trajectory anchor loader:

```text
rows              30
observation       30 x 72
hidden            30 x 128
reference_action  30 x 3
weight min        1.011909
weight max        50.000000
weight mean       3.227183
```

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_terminal_margin_recovery_anchor.py \
  tests/test_terminal_margin_retention_surface.py \
  tests/test_intervention_objectives.py \
  tests/test_outcome_intervention_optimize.py
```

Result:

```text
24 passed in 2.16s
```

## Interpretation

M278 shows that the M276 blocker was not that row16 is inherently unrecoverable.
The current hidden state still admits a small local action change that restores
terminal-margin slack. The failed M276 recipe was anchoring retention to an
already near-cliff action; M278 supplies a current-hidden recovery target.

This does not promote a driver checkpoint. It only admits a new no-PPO actor
update attempt using:

```text
M270 source-balanced objective
M275 retention trajectory anchor
M278 recovery action anchor
M183/M170 row16 hard gate first
```

PPO remains blocked.

## Decision

M278 completes the recovery-anchor probe.

Decision:

```text
admit_recovery_anchored_actor_update
```

Next step:

```text
m279-recovery-anchored-actor-update
```
