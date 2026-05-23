# M407 M406 Projection Replay Failure Row Audit

M407 audits the closed-loop replay failures from the M406 exact-feasible
projection candidate. It does not train, promote, lower thresholds, or change
actor inputs.

## Inputs

Candidate:

```text
runs/m406_repair_from_alpha01_s40_seed10137/candidate_checkpoint.pt
```

Replay artifacts:

```text
runs/m406_a01proj_m267_m264_first_replay/boundary_replay_rows.csv
runs/m406_a01proj_old_key_replay_gate/old_key_replay_comparison_rows.csv
```

Audit artifacts:

```text
runs/m407_projection_replay_failure_row_audit/summary.json
runs/m407_projection_replay_failure_row_audit/m267_m264_wrong_history_washout_rows.csv
runs/m407_projection_replay_failure_row_audit/old_key_accepted_regression_rows.csv
runs/m407_projection_replay_failure_row_audit/old_key_gap_tail_rows.csv
```

## M267/M264 Result

M406 fails M267/M264 because it makes the wrong-history branch safe, not because
the normal branch fails.

| Metric | Value |
| --- | ---: |
| rows | `17` |
| wrong-history washout rows | `16` |
| normal success regressions | `0` |
| physical pairs affected | `13` |
| candidate wrong-history margins positive | `16` |
| mean wrong-history margin delta | `+0.008327` |
| mean normal margin delta | `+0.007928` |
| targets affected | `15` future braking deceleration, `1` future yaw response |

The action change is systematic on wrong-history rows:

| Mean first-action delta | Value |
| --- | ---: |
| steer | `-0.004783` |
| throttle | `-0.008421` |
| brake | `+0.009823` |

In other words, the projection makes the wrong-history branch slightly more
conservative and it survives the obstacle. This destroys the counterfactual
self-ID proof even though exact M297/M270 do not regress.

## Old-Key Result

Old-key compact replay has `7` accepted regressions. They are source-diverse
across seed blocks `B`, `C`, `D`, and `E`.

| Metric | Value |
| --- | ---: |
| old-key compact rows | `40` |
| accepted regressions | `7` |
| wrong-history-safe regressions | `6` |
| normal-success regressions | `1` |
| gap-tail rows below `-0.0005` | `7` |
| gap-tail rows below `-0.002` | `3` |
| min candidate gap delta | `-0.016870` |

The only normal-branch failure is:

```text
9907|perturbed|27|18|10.500000|-1.200000|0.800000
```

The other six accepted regressions keep normal success but make wrong-history
rollouts too safe or outside the accepted boundary window.

## Classification

Primary classification:

```text
broad_wrong_history_washout_with_one_old_key_normal_branch_failure
```

Harness failure labels:

```text
proof_washout
objective_overfit
protected_key_window_failure
```

M407 confirms M406 is not a sparse single-row issue. The exact objectives allow
action changes that are small in the exact corpora but large enough in
closed-loop continuation to remove wrong-history collisions on most M267/M264
rows and six old-key rows.

## Decision

Do not repair directly and do not run PPO. The next step should design a
replay-aware projection residual that uses failed closed-loop rows or short
trajectory targets, rather than another exact-corpus scalar weight sweep:

```text
m408-replay-aware-projection-residual-design
```
