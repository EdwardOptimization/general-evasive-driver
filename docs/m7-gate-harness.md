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
make m7-corpus
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
make m7-gate
```

`make m7-gate` first refreshes the scenario corpus, then runs the benchmark and
history-ablation phases on the exact `seed` column from that corpus. The probe
phase still uses its own rollout seeds.

For a short command-path check:

```bash
make m7-gate-smoke
```

To require a new recurrent driver candidate such as M8, pass a driver
checkpoint. The gate still reports M7-A and M7-B as baselines, but the pass/fail
checks are evaluated on the named driver:

```bash
make m8-driver-gate-smoke
```

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

The first M8 smoke checkpoint is also rejected on the same label-balanced corpus
with probes skipped: success is 0.600 versus M5/M7 at 0.700, action/history
ablation drop is 0.000, and probes still need to run after real training. Its
useful signal is narrower: `aes_feasible` high-sideslip fraction drops to 0.000,
which suggests the stable-AES shaping is pointing in the intended direction
while the recurrent policy itself remains untrained.
