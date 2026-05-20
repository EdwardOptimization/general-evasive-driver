# M2 Circular Drift Results

Last updated: 2026-05-20

## Status

M2 has an initial passing result for circular drift tracking under randomized
vehicle and friction parameters.

Best checkpoint:

```text
runs/ppo_circle_m2_base_recover_20260520T122018Z_seed29/checkpoint.pt
```

The checkpoint is a local run artifact under `runs/` and is intentionally not
tracked by git.

## Training Sequence

The current best policy was produced by this sequence:

```bash
PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_circle_mvp.json \
  --total-steps 1000000 \
  --run-name ppo_circle_m2_feasible_1m

PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_circle_low_mu_finetune.json \
  --init-checkpoint runs/ppo_circle_m2_feasible_1m_20260520T115856Z_seed5/checkpoint.pt \
  --run-name ppo_circle_m2_feasible_low_mu_finetune

PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_circle_low_mu_finetune.json \
  --init-checkpoint runs/ppo_circle_m2_feasible_low_mu_finetune_20260520T120216Z_seed17/checkpoint.pt \
  --run-name ppo_circle_m2_low_mu_finetune2

PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_circle_base_finetune.json \
  --init-checkpoint runs/ppo_circle_m2_low_mu_finetune2_20260520T121647Z_seed17/checkpoint.pt \
  --run-name ppo_circle_m2_base_recover
```

## Benchmark

Command:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 200 \
  --policies heuristic checkpoint \
  --checkpoint runs/ppo_circle_m2_base_recover_20260520T122018Z_seed29/checkpoint.pt \
  --run-dir runs/benchmark_ppo_circle_m2_base_recover_200eval_20260520T122018Z_seed29
```

Overall result:

| policy | episodes | success_rate | return_mean | lateral_rmse_mean | beta_abs_error_mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| checkpoint | 200 | 0.975 | 992.35 | 1.356 | 0.340 |
| heuristic | 200 | 0.165 | 269.95 | 1.879 | 0.475 |

Friction bucket result:

| policy | mu_bucket | episodes | success_rate | return_mean | lateral_rmse_mean |
| --- | --- | ---: | ---: | ---: | ---: |
| checkpoint | low | 49 | 0.980 | 945.71 | 1.337 |
| checkpoint | medium | 74 | 0.986 | 1018.77 | 1.231 |
| checkpoint | high | 77 | 0.961 | 996.64 | 1.488 |
| heuristic | low | 49 | 0.204 | 271.68 | 1.860 |
| heuristic | medium | 74 | 0.189 | 305.34 | 1.828 |
| heuristic | high | 77 | 0.117 | 234.84 | 1.941 |

## Rollout Plots

Generate selected rollout traces and plots with:

```bash
PYTHONPATH=src python -m autodrift.rollout \
  --policy checkpoint \
  --checkpoint runs/ppo_circle_m2_base_recover_20260520T122018Z_seed29/checkpoint.pt \
  --seeds 7 37 65 \
  --out-dir runs/rollouts_ppo_circle_m2_base_recover_20260520T122018Z_seed29
```

Each selected seed writes:

- a per-step CSV trace;
- a summary JSON;
- a PNG with trajectory, sideslip, speed/lateral error, and actions.

## Engineering Findings

- The original clipped Gaussian policy learned a stochastic behavior that did
  not transfer to deterministic evaluation. Switching to a tanh-squashed action
  distribution and limiting log standard deviation fixed this failure mode.
- Low-friction circular tracking needs physically feasible target speeds. The
  environment now caps sampled speed targets by the friction-limited circular
  speed.
- Low-mu focused fine-tuning improves the hardest friction bucket, but it can
  hurt medium/high friction. The current best sequence uses low-mu fine-tuning
  followed by base-distribution recovery.
- Observation history support exists, but the current best M2 checkpoint uses
  the default single-frame observation. History stacking remains a likely M3
  tool for friction adaptation.

## Remaining M2 Risk

This is a single training-seed result. It is strong enough for the project to
move past the first circular-drift learning blocker, but before treating M2 as a
locked benchmark, repeat the training sequence with at least two more training
seeds and keep the same 200-seed evaluation set.
