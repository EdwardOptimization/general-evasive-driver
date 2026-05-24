# M542 Matched-History Variance Route Pilot

## Purpose

M542 runs the V1 one-seed 4096-step route pilot from the M541 config family:

```text
seed = 3540
levels = L0_current_observation, L2_finite_window, L3_online_gru
```

This milestone checks training route, checkpoint metadata, and smoke eval
outputs. It does not promote a checkpoint and does not make a stable baseline
ranking claim.

## Commands

```bash
PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo \
  --config configs/ppo_m541_matched_l0_variance_4096.json \
  --run-dir runs/m542_matched_l0_variance_seed3540 \
  --device cpu

PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo \
  --config configs/ppo_m541_matched_l2_variance_4096.json \
  --run-dir runs/m542_matched_l2_variance_seed3540 \
  --device cpu

PYTHONPATH=src OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -m autodrift.train_ppo \
  --config configs/ppo_m541_matched_l3_variance_4096.json \
  --run-dir runs/m542_matched_l3_variance_seed3540 \
  --device cpu
```

Aggregate artifact:

```text
runs/m542_matched_history_variance_route_pilot_summary/summary.json
runs/m542_matched_history_variance_route_pilot_summary/route_summary.csv
```

## Route Results

| Level | Run Dir | Return Mean | Steps Mean | Termination Rate | Lateral RMSE | Beta Abs Error |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| L0 current observation | `runs/m542_matched_l0_variance_seed3540` | `20.334296` | `60.2` | `1.0` | `1.933182` | `0.211867` |
| L2 finite window | `runs/m542_matched_l2_variance_seed3540` | `77.992665` | `69.4` | `0.2` | `0.664134` | `0.169140` |
| L3 online GRU | `runs/m542_matched_l3_variance_seed3540` | `21.645978` | `64.6` | `1.0` | `2.810300` | `0.166371` |

L2 is much stronger on this route eval, but this is still a single seed and a
training-route metric. The correct interpretation is route evidence only.

## Metadata Check

All three checkpoints record explicit matched-history metadata:

| Level | Actor Encoder | Actor History Length | Env History Length | Input Contract |
| --- | --- | ---: | ---: | --- |
| L0 | `mlp` | `1` | `1` | `P0_human_view_no_wheel_no_oracle` |
| L2 | `temporal_gru` | `4` | `4` | `P0_human_view_no_wheel_no_oracle` |
| L3 | `human_view_online_gru` | `1` | `1` | `P0_human_view_no_wheel_no_oracle` |

No actor input contract changed, and no promotion was performed.

## Interpretation

M542 passes the route-pilot gate:

- all three 4096-step configs run to completion;
- all three write checkpoints, config, train metrics, manifest, and eval summary;
- metadata confirms the intended P0 history-baseline levels;
- L2 is a strong finite-window competitor on seed `3540`.

This strengthens the M539 caution. The project should not frame L3 as clearly
superior to finite-window history until public frozen-source diagnostics and
multi-seed variance checks say so.

## Decision

```text
matched_variance_route_pilot_pass_l2_strong_admit_m543_public_surface_eval
```
