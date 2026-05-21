# M117 Source-Diverse Wrong-History Boundary Mining

M116 rejected M115 as duplicate-dominated: the `12` accepted wrong-history rows
collapsed to `3` physical source pairs and `1` boundary bucket. M117 tests the
cheapest next hypothesis:

```text
Maybe M115 failed diversity because its candidate filter or geometry sweep was
too narrow, not because the M113 surface is exhausted.
```

## Implementation

M117 reuses the M115 and M116 harnesses. It also adds relative geometry offsets
to `autodrift.wrong_history_boundary_relocation_surface`:

```text
--body-longitudinal-offsets
--body-lateral-offsets
```

These are relative to the source snapshot's current body-frame obstacle
position. They are safer than the earlier absolute `--body-laterals` diagnostic,
which overwrote the source geometry and destroyed the known M115 surface.

Focused validation:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  python -m pytest -q tests/test_wrong_history_boundary_relocation_surface.py

python -m compileall -q src tests
```

Result:

```text
7 passed
compileall passed
```

## Experiment A: Source-Only Expansion

This run removes M115's per-checkpoint/target top-k cap and uses all M113
wrong-history candidates.

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m62=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --outcome-csv runs/m113_matched_history_outcome_gate_seed9510/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-pairs-per-checkpoint-target 0 \
  --min-base-action-distance 0.0 \
  --target-normal-margins 0.005,0.01,0.02,0.05,0.10,0.15 \
  --half-width-inflations 0 \
  --min-margin-gap 0.02 \
  --min-accepted-wrong-rows 10 \
  --report-variants wrong_matched_history \
  --device cpu \
  --run-dir runs/m117_source_diverse_source_only_seed9510
```

Robustness:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_wrong_history_surface_robustness \
  --boundary-rows-csv runs/m117_source_diverse_source_only_seed9510/boundary_relocation_rows.csv \
  --control-checkpoint-label m62 \
  --margin-bucket-width 0.01 \
  --min-accepted-wrong-rows 10 \
  --min-physical-pairs 6 \
  --min-left-steps 5 \
  --min-checkpoints 2 \
  --min-targets 3 \
  --min-margin-buckets 2 \
  --min-success-drop-fraction 1.0 \
  --max-rows-per-pair-fraction 0.40 \
  --max-control-accepted-rows 0 \
  --run-dir runs/m117_source_diverse_source_only_robustness_seed9510
```

Result:

| Metric | Value |
| --- | ---: |
| Candidate rows | 360 |
| Replay rows | 2383 |
| Accepted wrong-history rows | 12 |
| Accepted physical pairs | 3 |
| Accepted margin buckets | 1 |
| Decision | reject duplicate-dominated |

Removing top-k did not expose new source pairs.

## Experiment B: Relative Lateral Expansion

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m62=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --outcome-csv runs/m113_matched_history_outcome_gate_seed9510/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-pairs-per-checkpoint-target 0 \
  --min-base-action-distance 0.0 \
  --target-normal-margins 0.005,0.01,0.02,0.05,0.10,0.15 \
  --half-width-inflations 0 \
  --body-lateral-offsets=-0.50,-0.25,0.0,0.25,0.50 \
  --min-margin-gap 0.02 \
  --min-accepted-wrong-rows 10 \
  --report-variants wrong_matched_history \
  --device cpu \
  --run-dir runs/m117_source_diverse_relative_lateral_seed9510
```

Robustness run:

```text
runs/m117_source_diverse_relative_lateral_robustness_seed9510
```

Result:

| Metric | Value |
| --- | ---: |
| Candidate rows | 360 |
| Replay rows | 11915 |
| Accepted wrong-history rows | 12 |
| Accepted physical pairs | 3 |
| Accepted margin buckets | 1 |
| Decision | reject duplicate-dominated |

Relative lateral offsets preserve the original surface but do not add diversity.

## Experiment C: Relative Longitudinal Expansion

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.wrong_history_boundary_relocation_surface \
  --checkpoint-policy m62=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m102=runs/m102_retention_actor_coupling_seed9550/optimized_checkpoint.pt \
  --checkpoint-policy m105=runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --outcome-csv runs/m113_matched_history_outcome_gate_seed9510/outcome_interventions.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --max-pairs-per-checkpoint-target 0 \
  --min-base-action-distance 0.0 \
  --target-normal-margins 0.005,0.01,0.02,0.05,0.10,0.15 \
  --half-width-inflations 0 \
  --body-longitudinal-offsets=-2.0,-1.0,0.0,1.0,2.0 \
  --min-margin-gap 0.02 \
  --min-accepted-wrong-rows 10 \
  --report-variants wrong_matched_history \
  --device cpu \
  --run-dir runs/m117_source_diverse_relative_longitudinal_seed9510
```

Robustness run:

```text
runs/m117_source_diverse_relative_longitudinal_robustness_seed9510
```

Result:

| Metric | Value |
| --- | ---: |
| Candidate rows | 360 |
| Replay rows | 11628 |
| Accepted wrong-history rows | 12 |
| Accepted physical pairs | 3 |
| Accepted margin buckets | 1 |
| Decision | reject duplicate-dominated |

Relative longitudinal offsets also preserve only the same original accepted
surface.

## Diagnostic: Absolute Lateral Positions

The earlier absolute lateral diagnostic was useful because it showed why M117
needed relative offsets:

```text
runs/m117_source_diverse_lateral_offsets_seed9510
```

It used fixed ego-frame `body_y` values:

```text
-1.0, -0.5, 0.0, 0.5, 1.0
```

Result:

```text
accepted_wrong_history_rows: 0
surface_found: false
```

This did not broaden the surface; it overwrote the source geometry and removed
the narrow M115 success-drop rows.

## Interpretation

M117 is negative.

The M115/M116 failure is not just a top-k artifact or a small local-geometry
search artifact. Even with all M113 candidates and relative lateral/longitudinal
neighborhood sweeps, accepted wrong-history rows remain the same `3` physical
source pairs and the same `0.000-0.010` normal-margin bucket.

The current M113-derived surface appears exhausted for robust wrong-history
training.

## Decision

Do not train a boundary-aware wrong-history objective from M113/M115 rows.

Next task: M118 should mine a fresh source-diverse matched-current-response
corpus before repeating M112/M113/M115. The priority should be new physical
source pairs, not additional obstacle-boundary tuning around the same pairs.
