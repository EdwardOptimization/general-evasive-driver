# M547 L3 Recurrent Repair Route Pilot

## Purpose

M547 runs the three M546 L3-only repair configs on seed `3540` and evaluates
their interval checkpoints using the M545 route-only checkpoint-selection rule.

This is a route pilot. It does not run public frozen-source eval and does not
promote a checkpoint.

## Artifacts

```text
runs/m547_l3_repair_fast_select_seed3540/
runs/m547_l3_repair_lr1e4_seed3540/
runs/m547_l3_repair_lr5e5_seed3540/
runs/m547_l3_recurrent_repair_route_pilot_summary/summary.json
runs/m547_l3_recurrent_repair_route_pilot_summary/route_checkpoint_eval.csv
runs/m547_l3_recurrent_repair_route_pilot_summary/train_peak_summary.csv
```

## Training Runs

All three runs completed and wrote final checkpoints, periodic checkpoints,
`train_metrics.csv`, `eval_summary.json`, and valid P0/L3 config metadata.

Final checkpoint route eval from training:

| Variant | Return Mean | Termination Rate | Lateral RMSE | Beta Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `fast_select` | `21.645978` | `1.000000` | `2.810300` | `0.166371` |
| `lr1e4` | `22.022030` | `1.000000` | `1.401758` | `0.223768` |
| `lr5e5` | `22.884914` | `1.000000` | `1.334784` | `0.223176` |

No final checkpoint passes the M545 route-health gate.

## Interval Checkpoint Selection

M547 evaluates `27` checkpoints total:

```text
3 variants x (8 interval checkpoints + final checkpoint)
episodes = 5
seed = 13540
```

M545 route-health gate:

```text
return_mean > 25.0
termination_rate < 1.0
```

Result:

```text
route_health_pass_count = 0 / 27
decision = route_health_reject_training_instability
```

Best checkpoint by the M545 route-only selection rule:

| Variant | Selected Step | Return Mean | Termination Rate | Lateral RMSE | Clearance Margin Mean | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `fast_select` | `1024` | `22.941196` | `1.000000` | `1.740065` | `-0.112931` | no |
| `lr1e4` | `2048` | `22.844632` | `1.000000` | `1.746500` | `-0.087499` | no |
| `lr5e5` | `4096` | `22.884914` | `1.000000` | `1.334784` | `-0.086878` | no |

The overall best checkpoint is `fast_select` step `1024`, but it still has
`termination_rate = 1.0`, so M547 rejects public frozen-source evaluation.

## Training Peak Audit

The training metrics show a sharper issue: all three variants still have their
best rollout-return step at `1792`, but `checkpoint_interval_steps = 512` does
not save a checkpoint at step `1792`.

| Variant | Best Train Step | Best Train Return | Best Train Termination | Final Train Return | Final Train Termination | Saved At Best Step |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `fast_select` | `1792` | `52.598733` | `0.750000` | `15.771149` | `1.000000` | no |
| `lr1e4` | `1792` | `67.155072` | `0.500000` | `16.740925` | `1.000000` | no |
| `lr5e5` | `1792` | `66.953277` | `0.500000` | `16.792478` | `1.000000` | no |

Therefore M547 does not prove that the lower-LR repair is useless. It proves
that the current repair route still has two problems:

1. the 512-step checkpoint cadence misses the best observed training update;
2. deterministic route eval of neighboring saved checkpoints remains weak.

## Interpretation

M547 rejects the current M546 repair family for public diagnostics. None of the
saved interval checkpoints reaches even the route-health threshold, so running
public frozen-source eval would violate the M545 gate order.

The next highest-leverage fix is not to tune public rows. It is to make the
checkpoint cadence update-aligned. PPO updates every `256` environment steps in
this setup, and the best training step is `1792`, which is reachable with a
`256`-step checkpoint cadence but not with the current `512` cadence.

After update-aligned checkpoints exist, the next route pilot should determine
whether the actual best training update passes deterministic route health. If it
still fails, the blocker shifts from checkpoint selection to an eval/training
objective mismatch.

## Decision

```text
route_health_reject_training_instability_admit_m548_update_aligned_checkpoint_configs
```
