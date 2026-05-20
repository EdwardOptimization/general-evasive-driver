# M6 Model-Based Baselines

Last updated: 2026-05-20

## Goal

M6 adds stronger non-RL baselines so the RL policy is not only compared against
weak tracking or braking policies. The first baseline is a friction-envelope
AES controller.

## Implemented Baseline

Policy name:

```text
envelope_aes
```

The controller uses:

- obstacle distance and required lateral offset;
- current speed and estimated time-to-collision;
- friction `mu` from scenario info;
- a lateral-acceleration envelope to choose steering intensity;
- light braking in `aes_feasible` scenarios and speed-preserving steering in
  `drift_required` scenarios.

This is not an NMPC controller. It is a compact fixed-parameter model-based
baseline that is stronger than the earlier heuristic AES baseline and cheap
enough to run in every benchmark.

## Benchmark

Command:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 100 \
  --policies aeb aes_heuristic envelope_aes heuristic checkpoint \
  --checkpoint runs/ppo_m5_obstacle_seed83/checkpoint.pt \
  --env-config configs/m5_obstacle_drift_required_eval.json \
  --run-dir runs/benchmark_ppo_m5_obstacle_seed83_drift_required_with_envelope_100eval
```

Result:

| policy | episodes | success_rate | collision_rate | obstacle_completion_rate | min_obstacle_clearance_mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| aeb | 100 | 0.050 | 0.950 | 0.050 | 1.577 |
| aes_heuristic | 100 | 0.500 | 0.500 | 0.500 | 1.865 |
| envelope_aes | 100 | 0.790 | 0.210 | 0.790 | 2.234 |
| heuristic | 100 | 0.190 | 0.810 | 0.190 | 1.669 |
| checkpoint | 100 | 0.860 | 0.140 | 0.860 | 2.180 |

Interpretation:

- `envelope_aes` is a meaningful stronger baseline: it improves drift-required
  success from `0.500` to `0.790` versus `aes_heuristic`.
- The RL checkpoint still leads on success and collision rate: `0.860` success
  and `0.140` collision rate.
- `envelope_aes` has slightly larger mean clearance than RL on this benchmark,
  so future RL improvements should avoid trading away clearance for speed.

## Next Steps

- Add a richer path/obstacle geometry benchmark before claiming generality.
- Consider NMPC only after the scenario and metric surfaces stabilize; the
  current fixed-envelope baseline is enough for the first MVP comparison.
