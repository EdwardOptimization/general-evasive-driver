# M1008 V4 Public Base Branch-Preserving Evaluator Sensitivity Audit

## Purpose

M1008 audits why the M1007 fixed one-step branch-ceiling and branch-separation
evaluator missed the M1004 closed-loop proof washout.

This milestone does not train, run PPO, use private holdout, or promote.

## Evidence Compared

Inputs:

```text
runs/m1007_v4_public_base_branch_preserving_temporal_repair_evaluator/branch_metric_rows.csv
runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight/*/boundary_replay_rows.csv
```

M1004 closed-loop replay says alpha `0.01` already loses rows `6` and `15`:

| row | base wrong margin | alpha 0.01 wrong margin | delta | success drop retained |
| --- | ---: | ---: | ---: | --- |
| 6 | -0.000117 | 0.000033 | +0.000151 | no |
| 15 | -0.000025 | 0.000171 | +0.000196 | no |

M1007 fixed one-step proxy says alpha `0.01` has no branch penalty:

| row | wrong logp delta | branch ceiling loss | first-action distance |
| --- | ---: | ---: | ---: |
| 6 | 0.000313 | 0.0 | 0.130873 |
| 15 | 0.000108 | 0.0 | 0.088308 |

The same mismatch persists at alpha `0.02`; alpha `0.05` loses rows `6`, `11`,
`15`, and `16` in replay, but still has zero M1007 branch loss.

## Root Cause

The failed M1007 proxy used coarse fixed-observation thresholds:

```text
epsilon_logp: 0.005 per step
separation floor: max(0.02, 0.75 * base_first_action_distance)
```

Those thresholds are too coarse for near-cliff rows whose wrong-history terminal
margins are already almost zero:

```text
row 6 base wrong margin:  -0.000117
row 15 base wrong margin: -0.000025
```

Alpha `0.01` changes wrong-history first actions only by about `1e-4` to
`3e-4`, but that is enough to cross the terminal margin boundary:

```text
row 6 wrong action delta:  steer +0.000145, throttle -0.000294, brake -0.000160
row 15 wrong action delta: steer +0.000073, throttle -0.000107, brake -0.000069
```

Therefore the problem is not that the branch signal is absent. It is that a
plain unscaled one-step logp/separation proxy is not margin-slack-aware.

## Failure Classification

```text
failure_type: metric_artifact
subtype: margin_slack_mismatch
```

Rejected alternatives:

```text
evaluator implementation bug: not primary
contract violation: no
training instability: no
behavior regression: not evaluated
```

The evaluator reconstructs rows and metrics correctly enough to show a trend at
alpha `0.2`, but its scale is mismatched to the near-zero terminal-margin proof
rows.

## Consequence

Do not use the M1007 fixed one-step branch proxy as a training objective.

The next residual must be explicitly margin-slack-weighted. It should protect
near-cliff wrong-history branches with much tighter trust-region pressure than
ordinary rows.

## Replacement Residual Direction

M1009 should design a margin-weighted rejected-branch trust-region residual:

```text
L_wrong_branch_trust =
  mean_i w_i * ||a_wrong_candidate_i - a_wrong_base_i||^2

w_i =
  source_weight_i / max(abs(base_wrong_margin_i), margin_floor)^2
```

Initial values:

```text
margin_floor: 1e-4
primary rows: 6, 15
secondary rows: 11, 16
full preflight rows: all M267/M264 rows
```

This is a constraint on the rejected proof branch, not a claim that the actor
should imitate wrong-history behavior as a deployable maneuver.

The exact evaluator should report both unweighted and margin-weighted drift:

```text
wrong_branch_action_l2
margin_weighted_wrong_branch_action_mse
normal_branch_action_l2
normal temporal sequence objective metrics
```

Acceptance for a future actor update should require:

```text
M997 temporal exact improvement retained
margin-weighted wrong-branch drift for rows 6 and 15 <= base + tiny tolerance
M267/M264 full preflight passes before any six-surface replay
```

## Decision

```text
branch_preserving_evaluator_sensitivity_audit_route_to_temporal_objective_branch_synthesis
```

The immediate next step must be branch synthesis because the temporal sequence
objective branch has reached the workflow synthesis cadence. That synthesis
should decide whether to continue with the margin-weighted trust-region residual
outlined above, pivot to trajectory targets, or stop this branch.

Next:

```text
m1009-v4-public-base-temporal-sequence-objective-branch-synthesis
```
