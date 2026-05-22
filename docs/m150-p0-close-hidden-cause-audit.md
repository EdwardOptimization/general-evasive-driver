# M150 P0-Close Hidden-Cause Audit

Date: 2026-05-22

## Question

M148 found target-divergent pairs that remain close under the current P0
human-view input. M149 rejected simple passive input expansion. M150 asks what
hidden/capability causes explain the remaining P0-close target divergence.

Hidden values are used only for offline diagnosis and training-time target
design. They are not actor inputs.

## Method

M150 consumes only M148 rows with:

```text
surface == p0_close_target_divergent
```

For each deterministic sample row it records hidden diagnostics:

```text
mu
mass_scale
inertia_scale
cg_shift
front_tire_stiffness_scale
rear_tire_stiffness_scale
drive_scale
brake_scale
steer_tau_scale
drive_tau_scale
```

Cause groups:

```text
friction: mu
braking_authority: brake_scale
drive_authority: drive_scale
tire_lateral_authority: front/rear tire stiffness scale
mass_geometry: mass scale, inertia scale, cg shift
actuator_delay: steer/drive tau scale
```

Target groups:

```text
future_braking_deceleration
future_yaw_response
future_lateral_accel_response
```

Metrics:

```text
hidden group standardized pair distance
future-envelope target distance
feature-target correlation
target-top / hidden-group-top overlap
dominant hidden group
dominant target
```

## Implementation

New module:

```text
src/autodrift/p0_close_hidden_cause_audit.py
```

New tests:

```text
tests/test_p0_close_hidden_cause_audit.py
```

The body-feedback collector now also writes hidden diagnostic fields to sample
rows. These fields remain explicitly diagnostic-only.

## Commands

Seed runs:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.p0_close_hidden_cause_audit \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --pair-csv runs/m148_p0_close_ambiguity_seed9480/accepted_pairs.csv \
  --episodes 40 --seed 9480 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --post-slip-beta-threshold 0.06 \
  --run-dir runs/m150_p0_close_hidden_cause_seed9480

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.p0_close_hidden_cause_audit \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --pair-csv runs/m148_p0_close_ambiguity_seed9481/accepted_pairs.csv \
  --episodes 40 --seed 9481 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --post-slip-beta-threshold 0.06 \
  --run-dir runs/m150_p0_close_hidden_cause_seed9481

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.p0_close_hidden_cause_audit \
  --mode run --env-config configs/m143_driver_like_profile_audit.json \
  --pair-csv runs/m148_p0_close_ambiguity_seed9482/accepted_pairs.csv \
  --episodes 40 --seed 9482 --policy heuristic --horizon-steps 15 \
  --sample-stride 3 --max-samples 1000 --post-slip-beta-threshold 0.06 \
  --run-dir runs/m150_p0_close_hidden_cause_seed9482
```

Aggregate:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.p0_close_hidden_cause_audit \
  --mode aggregate \
  --summary-jsons runs/m150_p0_close_hidden_cause_seed9480/summary.json,runs/m150_p0_close_hidden_cause_seed9481/summary.json,runs/m150_p0_close_hidden_cause_seed9482/summary.json \
  --run-dir runs/m150_p0_close_hidden_cause_multiseed
```

## Artifacts

```text
runs/m150_p0_close_hidden_cause_seed9480/summary.json
runs/m150_p0_close_hidden_cause_seed9481/summary.json
runs/m150_p0_close_hidden_cause_seed9482/summary.json
runs/m150_p0_close_hidden_cause_multiseed/summary.json
runs/m150_p0_close_hidden_cause_multiseed/hidden_group_summary.csv
runs/m150_p0_close_hidden_cause_multiseed/target_summary.csv
```

## Results

Hidden group summary over `240` P0-close pairs:

| Hidden group | Mean distance | Feature-target corr. | Top-overlap | Dominant fraction |
| --- | ---: | ---: | ---: | ---: |
| friction | 1.578262 | -0.183158 | 0.166667 | 0.341667 |
| braking authority | 1.197686 | -0.071742 | 0.200000 | 0.041667 |
| drive authority | 1.008890 | -0.053067 | 0.316667 | 0.158333 |
| tire lateral authority | 0.966373 | -0.001999 | 0.266667 | 0.062500 |
| mass geometry | 1.568961 | 0.409142 | 0.450000 | 0.300000 |
| actuator delay | 1.251474 | -0.229505 | 0.133333 | 0.095833 |

Target summary:

| Target | Mean abs diff | Mean z abs diff | Dominant fraction |
| --- | ---: | ---: | ---: |
| future braking deceleration | 1.138162 | 1.520156 | 0.304167 |
| future yaw response | 1.851881 | 2.601378 | 0.475000 |
| future lateral accel response | 2.260772 | 1.898658 | 0.220833 |

## Interpretation

The main future-envelope divergence is yaw response:

```text
future_yaw_response is dominant in 47.5% of pairs.
```

Friction is often the largest hidden difference, but it is not target-aligned
on this P0-close surface:

```text
friction dominant fraction: 34.2%
friction feature-target corr: -0.183
friction top-overlap: 16.7%
```

Mass/geometry is the strongest target-aligned hidden group:

```text
mass_geometry feature-target corr: 0.409
mass_geometry top-overlap: 45.0%
mass_geometry dominant fraction: 30.0%
```

This supports an important shift: do not train the next belief objective as
"predict mu". The better target is a capability envelope, especially yaw/lateral
authority under mass/inertia/cg variation.

## Decision

Complete M150 as a positive hidden-cause diagnostic:

- hidden parameters remain diagnostic/teacher-only and are not actor inputs;
- friction alone is not a sufficient self-ID target;
- yaw response and mass/geometry-sensitive capability are the strongest next
  belief-learning target surface;
- next step should build a capability-belief target dataset/objective for
  P0-close pairs rather than expanding passive inputs.
