# M700 Boundary Sensitivity-Scale Diagnostic Design

## Purpose

M700 designs a no-training diagnostic to answer why M698 found no accepted
fresh terminal-boundary rows.

Question:

```text
Was M698 empty because the snapshot window and perturbation scales were too
conservative, or because the base-policy distribution has no local
terminal-boundary sensitivity under reasonable first-action perturbations?
```

This milestone is design-only:

```text
no actor training
no objective design
no PPO
no checkpoint promotion
no actor-input change
```

## Background

M698 fresh sampling produced:

```text
episodes:                    512
snapshots_collected:        4056
normal_failed_rejected:     1360
too_safe_rejected:          2168
perturbation_evaluated_rows: 528
accepted_rows:                0
margin_sensitivity_p95:       0.001687
margin_sensitivity_max:       0.005952
threshold:                    0.020000
```

There were non-failed boundary-window candidates:

```text
wide_but_sensitive: 384
near_boundary:      112
terminal_cliff:      32
```

but the registered perturbation grid did not move terminal margin enough.

## Diagnostic Principle

M701 should not claim driver progress. It should produce a sensitivity map:

```text
window target x perturbation scale -> source result
```

The diagnostic should classify whether sensitivity appears at:

```text
plausible local override scales
stress but still interpretable scales
unrealistic override scales
no tested scale
```

Only plausible-scale rows can later admit source/objective design. Stress-scale
rows can guide simulator or scenario construction, but cannot become deployed
policy targets without a separate justification.

## Window Ladder

Run fresh sampling variants across:

```text
target_obstacle_distance:
  2.0
  1.0
  0.0
  -1.0

max_prepass_margin:
  0.50
  1.00
```

Keep:

```text
seed_start: 30000
seed_count: 512
surface configs: fresh, ood
snapshot_stride: 3
max_snapshots_per_episode: 8
max_continuation_steps: 40
```

If runtime is high, M701 may run a smoke subset first:

```text
seed_count: 64
```

but the registered diagnostic result should use the full 512-seed setting.

## Perturbation-Scale Ladder

Use four scale families:

```text
scale_local:
  steer:    +/- 0.04
  throttle: +/- 0.06
  brake:    +/- 0.06

scale_plausible:
  steer:    +/- 0.08
  throttle: +/- 0.12
  brake:    +/- 0.12

scale_stress:
  steer:    +/- 0.12
  throttle: +/- 0.20
  brake:    +/- 0.20

scale_unrealistic_probe:
  steer:    +/- 0.20
  throttle: +/- 0.35
  brake:    +/- 0.35
```

Each scale should include:

```text
single-axis perturbations
combined steer/brake pairs
base action as candidate_id=0
```

The diagnostic should keep the original acceptance threshold:

```text
margin_sensitivity >= 0.02
or risk_sensitivity >= 0.02
or success/collision/off-road/spin flip
```

Do not lower the threshold in M701. The point is to test scale sensitivity, not
to redefine positive evidence.

## Output Shape

M701 should write one root run directory:

```text
runs/m701_boundary_sensitivity_scale_diagnostic/
```

with per-variant subdirectories:

```text
target_2p0_margin_0p50_scale_local/
target_2p0_margin_0p50_scale_plausible/
...
```

Each sub-run can reuse the M698 sampler implementation.

Required aggregate artifacts:

```text
runs/m701_boundary_sensitivity_scale_diagnostic/summary.json
runs/m701_boundary_sensitivity_scale_diagnostic/variant_summary.csv
runs/m701_boundary_sensitivity_scale_diagnostic/scale_summary.csv
runs/m701_boundary_sensitivity_scale_diagnostic/window_summary.csv
runs/m701_boundary_sensitivity_scale_diagnostic/accepted_rows.csv
runs/m701_boundary_sensitivity_scale_diagnostic/rejected_rows.csv
```

`accepted_rows.csv` should include:

```text
variant_id
target_obstacle_distance
max_prepass_margin
scale_name
scale_class
snapshot_id
surface
seed
step
normal_margin
margin_sensitivity
risk_sensitivity
flip counts
history_action_critical flag
```

## Metrics

Per variant:

```text
episodes_attempted
snapshots_collected
prepass_rows
normal_failed_rejected
too_safe_rejected
perturbation_evaluated_rows
accepted_rows
trajectory_boundary_rows
history_action_critical_rows
margin_sensitivity_mean
margin_sensitivity_p95
margin_sensitivity_max
risk_sensitivity_mean
risk_sensitivity_p95
risk_sensitivity_max
success_flip_count
collision_flip_count
result_class
```

Aggregate:

```text
first_scale_with_any_accepted_rows
first_plausible_scale_with_any_accepted_rows
best_plausible_accepted_rows
best_stress_accepted_rows
best_unrealistic_accepted_rows
window_with_lowest_normal_failed_ratio
window_with_lowest_too_safe_ratio
```

## Result Classes

M701 should classify:

```text
scale_positive_plausible:
  plausible scale produces accepted rows with reasonable diversity

scale_positive_stress_only:
  only stress scale produces accepted rows

scale_positive_unrealistic_only:
  only unrealistic override scale produces accepted rows

windowing_failure:
  all windows are dominated by normal_failed or too_safe rows

scale_empty:
  evaluated rows exist but no tested scale produces sensitivity

implementation_failed:
  variant artifacts are incomplete
```

Only `scale_positive_plausible` can admit source/objective design.

## Negative-Result Interpretation

If `scale_empty`:

```text
the base policy and current scenario distribution are locally insensitive;
next step should be scenario construction or base capability improvement, not
another threshold tweak.
```

If `windowing_failure`:

```text
the sampler still misses the relevant obstacle interaction window; redesign
snapshot selection before changing objectives.
```

If `scale_positive_stress_only` or `scale_positive_unrealistic_only`:

```text
do not train on those rows as deployed action targets; use them to design better
scenario boundaries or to understand controllability limits.
```

If `scale_positive_plausible`:

```text
audit the rows for source diversity and then design a source-corpus export.
Do not jump directly to PPO.
```

## CLI Sketch

M701 can implement:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_sensitivity_scale_diagnostic \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --seed-start 30000 \
  --seed-count 512 \
  --target-obstacle-distance 2.0 \
  --target-obstacle-distance 1.0 \
  --target-obstacle-distance 0.0 \
  --target-obstacle-distance -1.0 \
  --max-prepass-margin 0.50 \
  --max-prepass-margin 1.00 \
  --scale local=0.04,0.06,0.06 \
  --scale plausible=0.08,0.12,0.12 \
  --scale stress=0.12,0.20,0.20 \
  --scale unrealistic_probe=0.20,0.35,0.35 \
  --snapshot-stride 3 \
  --max-snapshots-per-episode 8 \
  --max-continuation-steps 40 \
  --device cpu \
  --run-dir runs/m701_boundary_sensitivity_scale_diagnostic
```

The implementation should support a smaller smoke command:

```text
--seed-count 64
--target-obstacle-distance 1.0
--max-prepass-margin 1.00
--scale local=0.04,0.06,0.06
--scale plausible=0.08,0.12,0.12
```

## Decision

M700 admits M701 implementation.

Blocked until M701:

```text
source corpus export
objective design
actor update
PPO
checkpoint promotion
```

## Decision String

```text
boundary_sensitivity_scale_diagnostic_design_admit_m701
```

## Next

```text
m701-boundary-sensitivity-scale-diagnostic-implementation
```
