# M114 Near-Boundary Matched History Outcome Surface

## Question

M113 showed that M111/M112 pairs produce first-action differences but almost no
rollout outcome differences. M114 asks whether the same outcome data contains a
stricter near-boundary surface:

```text
matched current response
+ low normal clearance margin
+ intervention lowers clearance by at least a fixed margin gap
```

This is a corpus/surface mining step before any new objective or PPO run.

## Harness

Added:

```text
src/autodrift/near_boundary_outcome_surface.py
tests/test_near_boundary_outcome_surface.py
```

The harness consumes M113 `outcome_interventions.csv`, filters non-normal
variants by:

```text
normal_margin <= max_normal_margin
margin_gap >= min_margin_gap
normal_success == true
```

and writes:

```text
accepted_surface_rows.csv
surface_summary.csv
summary.json
```

The actor input contract is unchanged. This is only artifact selection from
already-run deployable-policy continuations.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.near_boundary_outcome_surface \
  --outcome-csv runs/m113_matched_history_outcome_gate_seed9510/outcome_interventions.csv \
  --max-normal-margin 0.20 \
  --min-margin-gap 0.02 \
  --min-accepted-rows 30 \
  --required-variants reset_hidden,wrong_matched_history \
  --run-dir runs/m114_near_boundary_outcome_surface_seed9510
```

Artifacts:

```text
runs/m114_near_boundary_outcome_surface_seed9510/summary.json
runs/m114_near_boundary_outcome_surface_seed9510/accepted_surface_rows.csv
runs/m114_near_boundary_outcome_surface_seed9510/surface_summary.csv
```

Top-level result:

```text
candidate_rows: 2160
accepted_rows: 119
unique_pairs: 51
surface_found: true
required_variants_present: false
required_variant_counts:
  reset_hidden: 39
  wrong_matched_history: 0
```

## Surface Summary

Aggregate:

```text
accepted_rows: 119
unique_pairs: 51
normal_margin_mean: 0.186675
normal_margin_min: 0.185399
normal_margin_max: 0.187538
variant_margin_mean: 0.156731
margin_gap_mean: 0.029944
margin_gap_max: 0.061959
success_drop_count: 0
normal_better_fraction: 1.0
```

Accepted rows by checkpoint and variant:

| checkpoint | reset_hidden | zero_current_response | delayed_history | wrong_matched_history |
| --- | ---: | ---: | ---: | ---: |
| M102 | 14 | 34 | 0 | 0 |
| M105 | 25 | 44 | 2 | 0 |
| M62 | 0 | 0 | 0 | 0 |

Accepted rows by target and variant:

| target | reset_hidden | zero_current_response | delayed_history |
| --- | ---: | ---: | ---: |
| future_braking_deceleration | 12 | 24 | 2 |
| future_lateral_accel_response | 23 | 42 | 0 |
| future_yaw_response | 4 | 12 | 0 |

## Interpretation

M114 is a partial positive surface-mining result.

Positive:

- near-boundary rows exist in the M113 data;
- normal margins are tightly near the boundary at about `0.185`-`0.188`;
- reset-hidden and zero-current-response variants can reduce clearance by more
  than `0.02`;
- the surface is large enough for a small objective or replay corpus if the goal
  is reset/zero-current degradation.

Negative:

- there are no `wrong_matched_history` accepted rows;
- there are no success drops;
- M62 contributes no accepted rows under this filter;
- this surface still does not prove wrong-history causal self-identification.

## Decision

Status: completed, partial positive.

Do not train a full driver on this surface yet. It is useful for reset/zeroed
history outcome pressure, but not for the stronger "wrong history induces wrong
vehicle belief" claim.

Next task: M115 should construct a boundary-relocated or obstacle-geometry
sensitivity surface targeted at wrong matched history. The acceptance condition
should require wrong-history margin loss or collision/mitigation degradation,
not only reset-hidden or zero-current-response loss.
