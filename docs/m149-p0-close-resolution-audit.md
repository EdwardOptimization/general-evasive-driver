# M149 P0-Close Resolution Audit

Date: 2026-05-22

## Question

M148 found many target-divergent pairs that are still close under the current P0
human-view input. M149 asks whether existing candidate signals resolve those
P0-close pairs in a target-aligned way:

```text
raw front/rear wheel-speed proxy
diagnostic local ground-speed slots
longer P0 history
```

This is a diagnostic gate. It does not promote any new actor input.

## Method

M149 consumes only M148 rows with:

```text
surface == p0_close_target_divergent
```

For each seed it reconstructs the same deterministic sample collection and
evaluates:

```text
p0_w25
p0_w50
p0_plus_raw_wheel_w25
p0_plus_raw_wheel_vparallel_w25
extra_raw_wheel_w25
extra_vparallel_w25
extra_raw_wheel_vparallel_w25
```

Resolution metrics:

```text
full/long-history candidate:
  distance_gain_vs_p0 >= 0.05
  and distance_ratio_vs_p0 >= 1.25

extra-only candidate:
  standardized extra-channel distance >= 0.25
```

Target alignment metrics:

```text
feature_target_corr
target_top_feature_top_overlap
```

The distinction is important: a signal can separate pairs without being aligned
with the future-envelope target gap.

## Implementation

New module:

```text
src/autodrift/p0_close_resolution_audit.py
```

New tests:

```text
tests/test_p0_close_resolution_audit.py
```

## Commands

Seed runs:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.p0_close_resolution_audit \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --pair-csv runs/m148_p0_close_ambiguity_seed9480/accepted_pairs.csv \
  --episodes 40 --seed 9480 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --base-history-window 25 \
  --long-history-window 50 --post-slip-beta-threshold 0.06 \
  --run-dir runs/m149_p0_close_resolution_seed9480

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.p0_close_resolution_audit \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --pair-csv runs/m148_p0_close_ambiguity_seed9481/accepted_pairs.csv \
  --episodes 40 --seed 9481 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --base-history-window 25 \
  --long-history-window 50 --post-slip-beta-threshold 0.06 \
  --run-dir runs/m149_p0_close_resolution_seed9481

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.p0_close_resolution_audit \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --pair-csv runs/m148_p0_close_ambiguity_seed9482/accepted_pairs.csv \
  --episodes 40 --seed 9482 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --base-history-window 25 \
  --long-history-window 50 --post-slip-beta-threshold 0.06 \
  --run-dir runs/m149_p0_close_resolution_seed9482
```

Aggregate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.p0_close_resolution_audit \
  --mode aggregate \
  --summary-jsons runs/m149_p0_close_resolution_seed9480/summary.json,runs/m149_p0_close_resolution_seed9481/summary.json,runs/m149_p0_close_resolution_seed9482/summary.json \
  --run-dir runs/m149_p0_close_resolution_multiseed
```

## Artifacts

```text
runs/m149_p0_close_resolution_seed9480/summary.json
runs/m149_p0_close_resolution_seed9481/summary.json
runs/m149_p0_close_resolution_seed9482/summary.json
runs/m149_p0_close_resolution_multiseed/summary.json
runs/m149_p0_close_resolution_multiseed/resolution_summary.csv
```

## Multiseed Results

Aggregate over `240` exported M148 P0-close pairs:

| Profile | Role | Resolved fraction | Feature-target corr. | Target-top/feature-top overlap |
| --- | --- | ---: | ---: | ---: |
| p0_w25 | base | 0.000000 | 0.390889 | 0.583333 |
| p0_w50 | long history | 0.233333 | -0.096056 | 0.166667 |
| p0 + raw wheel | full candidate | 0.037500 | 0.279495 | 0.466667 |
| p0 + raw wheel + vparallel | diagnostic full candidate | 0.120833 | 0.191947 | 0.400000 |
| extra raw wheel | extra only | 0.750000 | -0.046099 | 0.333333 |
| extra vparallel | diagnostic extra only | 0.750000 | -0.048411 | 0.333333 |
| extra raw wheel + vparallel | diagnostic extra only | 0.750000 | -0.047269 | 0.333333 |

## Interpretation

M149 is negative for simple input expansion:

```text
raw wheel and vparallel separate many P0-close pairs as extra-only signals,
but their distances are not target-aligned.
```

The full candidate results are weak:

```text
P0 + raw wheel resolves only 3.75%.
P0 + raw wheel + vparallel resolves 12.08%, but vparallel is diagnostic only.
```

Longer raw P0 history resolves more pairs (`23.33%`) but has negative
feature-target correlation and poor top-target/top-feature overlap. This means
the additional history distance is not reliably pointing at the future-envelope
gap.

## Decision

Complete M149 as a negative resolution audit:

- do not promote raw wheel;
- do not promote `v_parallel`;
- do not assume longer passive history solves P0-close ambiguity;
- next step should inspect hidden causes / capability-envelope causes of the
  P0-close pairs and then design active-identification or belief-learning
  targets, rather than expanding the actor input immediately.
