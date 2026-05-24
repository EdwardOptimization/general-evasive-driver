# M549 Update-Aligned L3 Route Pilot

## Purpose

M549 reruns the three L3 repair variants with update-aligned
`checkpoint_interval_steps = 256`, then evaluates all saved interval checkpoints
with the M545 route-only selection rule.

This is a route pilot. It does not run public frozen-source eval and does not
promote a checkpoint.

## Artifacts

```text
runs/m549_l3_repair_fast_select_ckpt256_seed3540/
runs/m549_l3_repair_lr1e4_ckpt256_seed3540/
runs/m549_l3_repair_lr5e5_ckpt256_seed3540/
runs/m549_update_aligned_l3_route_pilot_summary/summary.json
runs/m549_update_aligned_l3_route_pilot_summary/route_checkpoint_eval.csv
runs/m549_update_aligned_l3_route_pilot_summary/train_peak_summary.csv
```

## Training Runs

The three runs reproduce the M547 training metrics, which is expected because
M548 changed only checkpoint cadence.

Final checkpoint route eval from training:

| Variant | Return Mean | Termination Rate | Lateral RMSE | Beta Abs Error |
| --- | ---: | ---: | ---: | ---: |
| `fast_select_ckpt256` | `21.645978` | `1.000000` | `2.810300` | `0.166371` |
| `lr1e4_ckpt256` | `22.022030` | `1.000000` | `1.401758` | `0.223768` |
| `lr5e5_ckpt256` | `22.884914` | `1.000000` | `1.334784` | `0.223176` |

The final checkpoints remain route-unhealthy. The useful difference is that the
intermediate update steps are now saved.

## Checkpoint Coverage

M549 evaluates:

```text
3 variants x (16 interval checkpoints + final checkpoint) = 51 rows
episodes = 5
seed = 13540
```

The previously missed step `1792` is now saved for all three variants:

| Variant | Step 1792 Return | Step 1792 Termination | Step 1792 Margin | Pass |
| --- | ---: | ---: | ---: | --- |
| `fast_select_ckpt256` | `22.574747` | `1.000000` | `-0.078205` | no |
| `lr1e4_ckpt256` | `20.679310` | `1.000000` | `-0.127145` | no |
| `lr5e5_ckpt256` | `21.429875` | `1.000000` | `-0.135146` | no |

This answers the M548 question: the high rollout-return step is not itself a
deterministic route-health pass under the route eval seeds.

## Route Selection

M545 route-health gate:

```text
return_mean > 25.0
termination_rate < 1.0
```

M549 result:

```text
route_health_pass_count = 1 / 51
decision = route_health_pass
```

Best checkpoint by the M545 route-only selection rule:

| Variant | Selected Step | Return Mean | Termination Rate | Lateral RMSE | Clearance Margin Mean | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `fast_select_ckpt256` | `2816` | `27.858686` | `0.800000` | `2.697533` | `0.594595` | yes |
| `lr1e4_ckpt256` | `2048` | `22.844632` | `1.000000` | `1.746500` | `-0.087499` | no |
| `lr5e5_ckpt256` | `4096` | `22.884914` | `1.000000` | `1.334784` | `-0.086878` | no |

The route-selected checkpoint is:

```text
runs/m549_l3_repair_fast_select_ckpt256_seed3540/checkpoints/checkpoint_step_2816.pt
```

## Interpretation

M549 passes the route-health screen and admits public frozen-source diagnostics
for the route-selected checkpoint.

The positive result is narrow:

- update-aligned checkpointing found a route-healthy saved update;
- the route-healthy update is `fast_select_ckpt256` step `2816`, not the
  high-rollout-return step `1792`;
- lower-LR variants did not produce a route-health pass on this seed;
- no checkpoint is promoted from route evidence alone.

The next milestone should evaluate the selected checkpoint on the same public
M497/M487 frozen-source natural surfaces used by M543 and compare it against the
M542 L0/L2 and original M542 L3 seed-3540 checkpoints.

## Decision

```text
route_health_pass_admit_m550_public_surface_diagnostic
```
