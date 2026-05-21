# M25 Human-View GRU Smoke

Last updated: 2026-05-21

## Purpose

M25 is a smoke test for the M24 human-view contract. It is not a driver-quality
result. The goal is to prove that the 72-value observation, 3-channel action,
and `human_view_online_gru` actor can train end to end on GPU.

## Command

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m24_human_view_gru_driver.json \
  --total-steps 20480 \
  --seed 2024 \
  --device cuda \
  --run-dir runs/ppo_m25_human_view_gru_smoke_seed2024
```

Research harness run:

```text
runs/research/m25-human-view-gru-smoke_20260521T015946Z
```

## Result

- returncode: `0`;
- training device: `cuda`;
- final training step: 20480;
- checkpoint: `runs/ppo_m25_human_view_gru_smoke_seed2024/checkpoint.pt`;
- eval return mean: 50.532;
- eval steps mean: 53.700;
- eval termination rate: 0.500;
- eval lateral RMSE mean: 0.455;
- eval beta absolute error mean: 0.146.

Training metrics improved during the five updates:

| Step | Rollout return mean | Termination rate |
| ---: | ---: | ---: |
| 4096 | 33.691 | 0.841 |
| 8192 | 29.929 | 0.855 |
| 12288 | 36.479 | 0.747 |
| 16384 | 41.154 | 0.703 |
| 20480 | 43.762 | 0.648 |

## Conclusion

M25 passed as infrastructure. It proves the new human-view input/output
contract can train end to end with the online GRU actor. It does not prove the
policy is a good driver; termination is still high and the run is only 20k
steps.

The next step is a full M26 training run from scratch under the same contract,
followed by same-corpus obstacle benchmarks and response/hidden-state ablations.
