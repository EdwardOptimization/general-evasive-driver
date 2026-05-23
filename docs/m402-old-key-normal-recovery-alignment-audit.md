# M402 Old-Key Normal-Recovery Alignment Audit

M402 audits whether the M398 normal-margin recovery target is aligned with the
closed-loop old-key replay boundary after M400. It does not run PPO, promote a
checkpoint, lower thresholds, or change actor inputs.

## Active Case

```text
9958|perturbed|39|36|9.500000|-1.200000|0.900000
```

M398 recovery target:

| Action | Steer | Throttle | Brake |
| --- | ---: | ---: | ---: |
| M398 base action | 0.631576 | 0.126190 | 0.172466 |
| M398 recovery action | 0.591576 | 0.066190 | 0.252466 |
| Delta | -0.040000 | -0.060000 | +0.080000 |

The local recovery target is strong:

```text
baseline margin: 0.000086
selected recovery margin: 0.002443
margin improvement: 0.002358
action L2: 0.107703
```

## Policy Action Alignment

Audit artifact:

```text
runs/m402_old_key_recovery_alignment_audit/alignment_rows.csv
```

| Policy | Preferred steer | Preferred throttle | Preferred brake | Distance to recovery action | Normal margin | Accepted |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| m395_base | 0.631576 | 0.126190 | 0.172466 | 0.107703 | +0.000085545 | true |
| m399s02_a050 | 0.631598 | 0.126266 | 0.172417 | 0.107791 | +0.000000279 | true |
| m399s02_a100 | 0.631621 | 0.126343 | 0.172367 | 0.107879 | -0.000085082 | false |
| m399s02_endpoint | 0.632030 | 0.127719 | 0.171475 | 0.109463 | -0.001624640 | false |

The repair direction barely moves the preferred action, and its movement is not
toward the M398 recovery target. The target asks for less steer, less throttle,
and more brake, but the s02 endpoint moves toward slightly more steer, more
throttle, and less brake.

## Interpretation

The M398 target is not stale and does not need to be re-mined first. It is a
valid one-step local action that improves terminal margin. The issue is that the
M399 exact repair objective does not express that target strongly enough at the
active old-key row. The selected alpha `0.05` already consumes most of the
normal-margin slack, and alpha `0.10` crosses zero even though the policy action
is still almost identical to the base action.

Classify:

```text
recovery_residual_underweighted_vs_closed_loop_boundary
```

Not classified as:

```text
target_refresh_needed
wrong_history_sensitivity_loss
actor_input_contract_issue
PPO_instability
```

## Decision

The next task should run a no-PPO recovery-weight sweep from the M400 base. The
sweep should increase old-key recovery pressure enough to test whether the
policy action can move toward the M398 target while retaining M267/M264
wrong-history proof, cumulative old-key replay, and exact M297/M270
no-regression.

Admit:

```text
m403-old-key-normal-recovery-weight-sweep
```
