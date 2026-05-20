# M7 Gate Harness

Last updated: 2026-05-21

## Purpose

The M7 gate harness turns the current validation protocol into a repeatable
command. It is not a training command. It evaluates whether a frozen M7 policy
has actually improved as a driver-like closed-loop operator.

The gate checks four claims:

- M7 beats the M5 checkpoint on the shared held-out benchmark.
- M7 performance degrades when action history or temporal order is removed.
- M7 handles `aes_feasible` cases without excessive high-sideslip behavior.
- M7 actor latents contain temporal information that is lost when history is
  shuffled.

## Scenario Corpus

Build a label-balanced seed corpus:

```bash
conda run -n autodrift python -m autodrift.scenario_corpus \
  --env-config configs/m7_obstacle_aes_weighted_holdout_eval.json \
  --seed-start 1300 \
  --per-label 20 \
  --max-candidates 1000 \
  --run-dir runs/scenario_corpus_m7_aes_weighted_seed1300
```

Current result:

| label | episodes |
| --- | ---: |
| `aes_feasible` | 20 |
| `drift_required` | 20 |
| `unavoidable` | 20 |

Artifacts:

- `scenario_corpus.csv`;
- `label_summary.csv`;
- `vehicle_road_summary.csv`;
- `summary.json`;
- `manifest.json`.

## M7 Gate

Run the complete M7 validation gate:

```bash
conda run -n autodrift python -m autodrift.m7_gate \
  --env-config configs/m7_obstacle_aes_weighted_holdout_eval.json \
  --seed-csv runs/scenario_corpus_m7_aes_weighted_seed1300/scenario_corpus.csv \
  --episodes 100 \
  --seed 900 \
  --probe-episodes 100 \
  --probe-seed 1200 \
  --probe-epochs 160 \
  --device cpu \
  --run-dir runs/m7_gate_aes_weighted_corpus_seed1300
```

If `--seed-csv` is set, the benchmark and history-ablation phases use the
exact `seed` column from the corpus instead of a contiguous seed range. The
probe phase still uses its own rollout seeds.

Current result:

| check | result |
| --- | --- |
| `success_beats_m5` | fail |
| `ablation_drop_present` | fail |
| `aes_feasible_sideslip_ok` | fail |
| `probe_temporal_lift_present` | fail |

Overall status: `needs_iteration`.

Key metrics:

| metric | value |
| --- | ---: |
| `m5_success_rate` | 0.700 |
| `m7a_success_rate` | 0.700 |
| `m7b_success_rate` | 0.700 |
| `best_m7_success_delta_vs_m5` | 0.000 |
| `best_ablation_drop` | 0.000 |
| `m7a_aes_feasible_high_sideslip` | 0.292 |
| `m7b_aes_feasible_high_sideslip` | 0.171 |
| `best_probe_temporal_lift` | 0.019 |

Artifacts:

- `benchmark_comparison/`;
- `history_ablation/`;
- `latent_probe_m7a/`;
- `latent_probe_m7b/`;
- `gate_summary.md`;
- `summary.json`;
- `manifest.json`;
- `logs/`.

## Interpretation

The gate correctly rejects the current M7 checkpoints. On the label-balanced
corpus, M7-A and M7-B tie M5 on aggregate success rather than beating it, and
they still do not prove driver-like closed-loop adaptation.

This is the intended behavior of the harness: it should prevent a small success
rate improvement from being mistaken for a validated self-identifying operator.
