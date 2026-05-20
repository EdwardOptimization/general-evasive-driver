# M2 Circular Drift Results

Last updated: 2026-05-20

## Status

M2 has an initial passing result for circular drift tracking under randomized
vehicle and friction parameters.

Best checkpoint:

```text
runs/ppo_circle_m2_seed113_recover2/checkpoint.pt
```

The checkpoint is a local run artifact under `runs/` and is intentionally not
tracked by git.

## Training Sequence

The current best policy was produced by an extended low-mu/base recovery
sequence:

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

An independent training trajectory starting from seed 101 needed one additional
low-mu/base recovery cycle and produced the current best checkpoint:

```bash
PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_circle_mvp.json \
  --total-steps 1000000 \
  --seed 101 \
  --run-dir runs/ppo_circle_m2_seed101_main

PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_circle_low_mu_finetune.json \
  --seed 103 \
  --init-checkpoint runs/ppo_circle_m2_seed101_main/checkpoint.pt \
  --run-dir runs/ppo_circle_m2_seed103_low1

PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_circle_low_mu_finetune.json \
  --seed 107 \
  --init-checkpoint runs/ppo_circle_m2_seed103_low1/checkpoint.pt \
  --run-dir runs/ppo_circle_m2_seed107_low2

PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_circle_base_finetune.json \
  --seed 109 \
  --init-checkpoint runs/ppo_circle_m2_seed107_low2/checkpoint.pt \
  --run-dir runs/ppo_circle_m2_seed109_recover

PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_circle_low_mu_finetune.json \
  --seed 111 \
  --init-checkpoint runs/ppo_circle_m2_seed109_recover/checkpoint.pt \
  --run-dir runs/ppo_circle_m2_seed111_low3

PYTHONPATH=src python -m autodrift.train_ppo \
  --config configs/ppo_circle_base_finetune.json \
  --seed 113 \
  --init-checkpoint runs/ppo_circle_m2_seed111_low3/checkpoint.pt \
  --run-dir runs/ppo_circle_m2_seed113_recover2
```

## Benchmark

Command:

```bash
PYTHONPATH=src python -m autodrift.benchmark \
  --episodes 200 \
  --policies heuristic checkpoint \
  --checkpoint runs/ppo_circle_m2_seed113_recover2/checkpoint.pt \
  --run-dir runs/benchmark_ppo_circle_m2_seed113_recover2_200eval
```

Overall result:

| policy | episodes | success_rate | return_mean | lateral_rmse_mean | beta_abs_error_mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| checkpoint | 200 | 1.000 | 1128.53 | 0.888 | 0.278 |
| heuristic | 200 | 0.165 | 269.95 | 1.879 | 0.475 |

Friction bucket result:

| policy | mu_bucket | episodes | success_rate | return_mean | lateral_rmse_mean |
| --- | --- | ---: | ---: | ---: | ---: |
| checkpoint | low | 49 | 1.000 | 1037.30 | 1.022 |
| checkpoint | medium | 74 | 1.000 | 1140.54 | 0.822 |
| checkpoint | high | 77 | 1.000 | 1175.05 | 0.867 |
| heuristic | low | 49 | 0.204 | 271.68 | 1.860 |
| heuristic | medium | 74 | 0.189 | 305.34 | 1.828 |
| heuristic | high | 77 | 0.117 | 234.84 | 1.941 |

Replication benchmark:

| checkpoint | benchmark | success_rate | low | medium | high |
| --- | --- | ---: | ---: | ---: | ---: |
| `runs/ppo_circle_m2_base_recover_20260520T122018Z_seed29/checkpoint.pt` | `runs/benchmark_ppo_circle_m2_base_recover_200eval_20260520T122018Z_seed29` | 0.975 | 0.980 | 0.986 | 0.961 |
| `runs/ppo_circle_m2_seed113_recover2/checkpoint.pt` | `runs/benchmark_ppo_circle_m2_seed113_recover2_200eval` | 1.000 | 1.000 | 1.000 | 1.000 |

## Rollout Plots

Generate selected rollout traces and plots with:

```bash
PYTHONPATH=src python -m autodrift.rollout \
  --policy checkpoint \
  --checkpoint runs/ppo_circle_m2_seed113_recover2/checkpoint.pt \
  --seeds 7 37 65 \
  --out-dir runs/rollouts_ppo_circle_m2_seed113_recover2
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

The current result is strong enough to move past the first circular-drift
learning blocker. Before freezing M2 as a release benchmark, make the
low-mu/base recovery sequence shorter and less manual.
