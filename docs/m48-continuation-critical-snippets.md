# M48 Continuation-Critical Snippets

Last updated: 2026-05-21

## Motivation

M47 localized M46's mixed result to two seeds:

- seed 4327: M46 improves a high-friction unavoidable case;
- seed 3037: M46 regresses a low-friction unavoidable case.

M48 adds per-step continuation snippets so the next objective can be based on
closed-loop trajectory evidence rather than static hidden-vector separation.

## Harness

New CLI:

```text
autodrift.continuation_snippets
```

It traces specified seeds and policies step by step and writes:

- `steps.csv`: per-step info, action, reward terms, clearance margin, terminal
  flags;
- `episodes.csv`: episode outcome summary;
- `action_delta_summary.csv`: per-seed action trajectory distance versus a
  selected baseline policy;
- `observations.npz`: deployed observations and actions for each traced step;
- `manifest.json`.

## Command

```bash
conda run -n autodrift python -m autodrift.continuation_snippets \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --seed 4327 \
  --seed 3037 \
  --checkpoint-policy m30_053=runs/ppo_m30_mixed_matched_response_seed1330/checkpoints/checkpoint_step_53248.pt \
  --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --checkpoint-policy m42_028=runs/ppo_m42_hidden_contrast_seed1842/checkpoints/checkpoint_step_28672.pt \
  --checkpoint-policy m46_077=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_77824.pt \
  --checkpoint-policy m46_200=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_200000.pt \
  --baseline-policy m37_102 \
  --device cpu \
  --run-dir runs/m48_continuation_snippets_changed_seeds
```

## Outcome Summary

| Seed | Policy | Success | Terminal reason | Return | Min clearance | Collision radius | Margin |
| ---: | --- | ---: | --- | ---: | ---: | ---: | ---: |
| 4327 | M30_053 | 0 | collision | 0.507 | 1.414614 | 1.467856 | -0.053241 |
| 4327 | M37_102 | 0 | collision | 0.441 | 1.464763 | 1.467856 | -0.003093 |
| 4327 | M42_028 | 0 | collision | 0.451 | 1.465120 | 1.467856 | -0.002736 |
| 4327 | M46_077 | 1 | obstacle_completed | 54.718 | 1.468718 | 1.467856 | 0.000862 |
| 4327 | M46_200 | 1 | obstacle_completed | 54.033 | 1.470344 | 1.467856 | 0.002488 |
| 3037 | M30_053 | 1 | obstacle_completed | 89.048 | 1.678908 | 1.518286 | 0.160622 |
| 3037 | M37_102 | 1 | obstacle_completed | 91.586 | 1.527674 | 1.518286 | 0.009387 |
| 3037 | M42_028 | 1 | obstacle_completed | 91.425 | 1.559222 | 1.518286 | 0.040936 |
| 3037 | M46_077 | 0 | collision | 36.802 | 1.515931 | 1.518286 | -0.002355 |
| 3037 | M46_200 | 0 | collision | 35.844 | 1.510616 | 1.518286 | -0.007670 |

Both M46 outcome flips are near-boundary clearance events, not robust margins.
M46 wins seed 4327 by less than 3 mm and loses seed 3037 by less than 8 mm.

## Action Comparison

Action trajectory distance versus M37_102:

| Seed | Candidate | Common steps | First action distance | Mean action distance | Max action distance |
| ---: | --- | ---: | ---: | ---: | ---: |
| 4327 | M42_028 | 35 | 0.0886 | 0.0905 | 0.1029 |
| 4327 | M46_077 | 35 | 0.0732 | 0.0738 | 0.1431 |
| 4327 | M46_200 | 35 | 0.0980 | 0.0662 | 0.1087 |
| 3037 | M42_028 | 69 | 0.0546 | 0.1193 | 0.1812 |
| 3037 | M46_077 | 60 | 0.0827 | 0.0667 | 0.0827 |
| 3037 | M46_200 | 59 | 0.0843 | 0.0661 | 0.1291 |

M46 does not make a large, clearly different maneuver. It moves a near-collision
trajectory by millimeters. This explains why M46 can improve one critical seed
while regressing another: the objective changes the boundary but does not create
a robust clearance policy.

## Interpretation

The next gate should include clearance margin, not only binary success. A policy
that passes by 0.000862 m is not meaningfully robust. M49 should extend the
benchmark/gate layer to report collision radius and min-clearance margin, then
use that metric for critical-seed selection and checkpoint promotion.

Current best remains M37_102 because it keeps the broad aggregate gate and has
positive low-friction clearance margin on seed 3037.
