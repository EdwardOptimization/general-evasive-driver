# M451 Challenge Config Sampling Robustness Repair

## Purpose

M450 failed before policy evaluation because both M449 challenge configs could
hit `RuntimeError: failed to sample an obstacle scenario matching the configured
filters` at seed block `9900`. M451 does not train or promote a checkpoint. It
creates replacement challenge configs under new M451 names, keeps the M449
artifacts intact as failure evidence, and validates sampling across seed blocks
`9800`, `9900`, and `10000`.

## Config Changes

New configs:

- `configs/m451_challenge_near_threshold_robust_zero_relvel.json`
- `configs/m451_challenge_late_high_energy_robust_zero_relvel.json`

Both configs preserve the mainline human-view/no-wheel contract:

- `history_length = 1`
- `action_history_mode = full`
- `obstacle_relative_velocity_mode = zero`
- no wheel, slip, tire-force, hidden-parameter, oracle-feasibility, TTC, or
  reference-trajectory actor inputs

The repair is intentionally limited to scenario sampling parameters:

- wider obstacle distance and width ranges;
- less restrictive `max_threshold_score`;
- `min_time_after_friction_step = 0.0`;
- slightly wider track width for the near-threshold variant;
- retained low-mu, actuator-lag, brake-scale, tire-scale, and friction-step
  randomization.

## Reset Stress

Reset-only stress tested 128 resets per config and seed block.

| config | seed | resets | labels | mu range |
| --- | ---: | ---: | --- | --- |
| near | 9800 | 128 | `drift_required=79`, `aes_feasible=18`, `unavoidable=31` | `0.246529-0.746649` |
| near | 9900 | 128 | `aes_feasible=21`, `drift_required=71`, `unavoidable=36` | `0.224446-0.745645` |
| near | 10000 | 128 | `aes_feasible=17`, `drift_required=72`, `unavoidable=39` | `0.224446-0.745645` |
| late | 9800 | 128 | `drift_required=63`, `unavoidable=48`, `aes_feasible=17` | `0.225027-0.696839` |
| late | 9900 | 128 | `drift_required=63`, `unavoidable=46`, `aes_feasible=19` | `0.204195-0.695892` |
| late | 10000 | 128 | `drift_required=66`, `unavoidable=44`, `aes_feasible=18` | `0.204195-0.695892` |

All reset stress runs completed without sampling failure.

## Benchmark Smoke

Each smoke ran 16 episodes with `heuristic` and M399 base:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.benchmark \
  --env-config configs/m451_challenge_near_threshold_robust_zero_relvel.json \
  --episodes 16 \
  --seed 9800 \
  --policies heuristic \
  --checkpoint-policy m399_base=runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --device cpu \
  --run-dir runs/m451_near_robust_smoke_seed9800
```

The same command shape was run for both configs and seeds `9800`, `9900`, and
`10000`.

| config | seed | policy | episodes | success | collision | mean margin | min margin | return |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| near | 9800 | heuristic | 16 | `0.3750` | `0.6250` | `0.518179` | `-0.251144` | `53.289032` |
| near | 9800 | m399_base | 16 | `1.0000` | `0.0000` | `2.671879` | `0.195546` | `80.350211` |
| near | 9900 | heuristic | 16 | `0.5000` | `0.5000` | `0.165202` | `-0.326149` | `63.756585` |
| near | 9900 | m399_base | 16 | `1.0000` | `0.0000` | `2.259275` | `0.720055` | `88.784514` |
| near | 10000 | heuristic | 16 | `0.0625` | `0.8750` | `0.053209` | `-0.198468` | `31.170284` |
| near | 10000 | m399_base | 16 | `0.8750` | `0.1250` | `2.015071` | `-0.035667` | `75.983426` |
| late | 9800 | heuristic | 16 | `0.3750` | `0.6250` | `0.435283` | `-0.205846` | `51.425048` |
| late | 9800 | m399_base | 16 | `0.8125` | `0.1875` | `1.918425` | `-0.082780` | `74.475146` |
| late | 9900 | heuristic | 16 | `0.3750` | `0.6250` | `0.283093` | `-0.231552` | `52.164044` |
| late | 9900 | m399_base | 16 | `0.9375` | `0.0625` | `1.952072` | `-0.065793` | `82.649197` |
| late | 10000 | heuristic | 16 | `0.1250` | `0.8125` | `0.007819` | `-0.258869` | `36.719953` |
| late | 10000 | m399_base | 16 | `0.8750` | `0.1250` | `1.717798` | `-0.134576` | `80.056231` |

Run directories:

- `runs/m451_near_robust_smoke_seed9800`
- `runs/m451_near_robust_smoke_seed9900`
- `runs/m451_near_robust_smoke_seed10000`
- `runs/m451_late_robust_smoke_seed9800`
- `runs/m451_late_robust_smoke_seed9900`
- `runs/m451_late_robust_smoke_seed10000`

## Decision

M451 passes as an infrastructure/generalization repair. The robust configs pass
multi-seed reset stress and tiny benchmark smoke without actor contract changes,
training, or checkpoint promotion.

The difficulty tradeoff is acceptable: the filters are less brittle than M449,
but the configs still contain low-mu and high-energy cases, keep a mixed
`aes_feasible` / `drift_required` / `unavoidable` label distribution, and keep
heuristic success substantially below M399 in the smoke tests.

Next blocker:

```text
m452-robust-challenge-response-ablation-benchmark
```

M452 should rerun the M450 response/history ablation benchmark using the M451
robust configs.
