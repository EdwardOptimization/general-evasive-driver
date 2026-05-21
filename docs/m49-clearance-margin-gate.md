# M49: Clearance-Margin Gate

## Motivation

M48 showed that the M46 outcome flips are not robust driver improvements.
They are millimeter-scale obstacle-clearance boundary cases:

- seed 4327: M46 changes a collision into a near miss by roughly 1 to 2 mm;
- seed 3037: M46 changes a success into a collision by roughly 2 to 8 mm.

Binary success is therefore too coarse for the next driver gate. A policy that
barely crosses the collision boundary should not be treated the same as a
policy that preserves useful clearance.

M49 promotes clearance margin to a first-class evaluation and benchmark metric.

## Metric

For obstacle tasks:

```text
obstacle_collision_radius =
    ego_half_width + obstacle_half_width

min_clearance_margin =
    min_obstacle_clearance - obstacle_collision_radius
```

Interpretation:

- positive margin: the episode avoided collision with that much clearance;
- zero margin: the trajectory touched the collision boundary;
- negative margin: the episode collided by that penetration margin.

The metric is reported only from environment/evaluation outputs. It is not an
actor observation and does not change the human-view policy contract.

## Implementation

Code changes:

- `src/autodrift/env.py` now reports `obstacle_collision_radius` and
  `min_clearance_margin` in `info`;
- `src/autodrift/evaluate.py` records both fields in per-episode rows and
  adds margin mean/min summary values;
- `src/autodrift/benchmark.py` includes optional policy/bucket summary columns
  when those episode fields are present;
- `src/autodrift/seed_delta_audit.py` includes collision radius in context and
  margin delta in per-seed and policy summaries.

Tests:

- `tests/test_env.py` covers obstacle collision-radius and finite margin info;
- `tests/test_evaluate.py` covers propagation into episode rows;
- `tests/test_benchmark.py` covers benchmark summary columns.

Targeted validation:

```bash
conda run -n autodrift pytest -q \
  tests/test_env.py \
  tests/test_evaluate.py \
  tests/test_benchmark.py \
  tests/test_seed_delta_audit.py \
  tests/test_continuation_snippets.py
```

Result: `42 passed`.

## Changed-Seed Benchmark

Seed file:

```text
runs/m49_changed_seed_margin_benchmark/changed_seeds.csv
```

Benchmark command:

```bash
conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --seed-csv runs/m49_changed_seed_margin_benchmark/changed_seeds.csv \
  --checkpoint-policy m30_053=runs/ppo_m30_mixed_matched_response_seed1330/checkpoints/checkpoint_step_53248.pt \
  --checkpoint-policy m37_102=runs/ppo_m37_multistep_response_aux_seed1637/checkpoints/checkpoint_step_102400.pt \
  --checkpoint-policy m42_028=runs/ppo_m42_hidden_contrast_seed1842/checkpoints/checkpoint_step_28672.pt \
  --checkpoint-policy m46_077=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_77824.pt \
  --checkpoint-policy m46_200=runs/ppo_m46_paired_hidden_action_contrast_seed2046/checkpoints/checkpoint_step_200000.pt \
  --device cpu \
  --run-dir runs/m49_changed_seed_margin_benchmark
```

Policy summary:

| Policy | Success | Return | Min margin mean | Min margin min |
| --- | ---: | ---: | ---: | ---: |
| heuristic | 0.0000 | 9.498 | -0.063399 | -0.078945 |
| m30_053 | 0.5000 | 44.777 | 0.053690 | -0.053241 |
| m37_102 | 0.5000 | 46.014 | 0.003147 | -0.003093 |
| m42_028 | 0.5000 | 45.938 | 0.019100 | -0.002736 |
| m46_077 | 0.5000 | 45.760 | -0.000747 | -0.002355 |
| m46_200 | 0.5000 | 44.939 | -0.002591 | -0.007670 |
| random | 0.0000 | 8.241 | -0.171431 | -0.186185 |

Artifacts:

- `runs/m49_changed_seed_margin_benchmark/episodes.csv`;
- `runs/m49_changed_seed_margin_benchmark/policy_summary.csv`;
- `runs/m49_changed_seed_margin_benchmark/manifest.json`.

## Margin Delta Audit

Command:

```bash
conda run -n autodrift python -m autodrift.seed_delta_audit \
  --episodes-csv runs/m49_changed_seed_margin_benchmark/episodes.csv \
  --baseline-policy m37_102 \
  --candidate-policy m46_077 \
  --candidate-policy m46_200 \
  --run-dir runs/m49_changed_seed_margin_delta_audit
```

Summary versus M37_102:

| Candidate | Pairs | Success delta | Improved | Regressed | Margin delta mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| m46_077 | 2 | 0.0000 | 1 | 1 | -0.003894 |
| m46_200 | 2 | 0.0000 | 1 | 1 | -0.005739 |

Artifacts:

- `runs/m49_changed_seed_margin_delta_audit/seed_deltas.csv`;
- `runs/m49_changed_seed_margin_delta_audit/policy_delta_summary.csv`;
- `runs/m49_changed_seed_margin_delta_audit/group_delta_summary.csv`;
- `runs/m49_changed_seed_margin_delta_audit/manifest.json`.

## Conclusion

M49 does not produce a stronger checkpoint. It upgrades the measurement path so
future gates can reject fragile near misses. On the two M48 changed seeds, M46
matches M37_102 in binary success rate but has worse mean clearance margin:

- M46_077: `-0.003894 m` margin delta versus M37_102;
- M46_200: `-0.005739 m` margin delta versus M37_102.

The current best remains `m37_102`.

## Next Step

M50 should mine a larger margin-critical corpus from M38, broad same-seed, and
new randomized obstacle sweeps. The corpus should include:

- successes with small positive margin;
- collisions with small negative margin;
- seeds where policy success is unchanged but margin worsens materially;
- seeds where M46-style objectives improve one road/actuator bucket but hurt
  another bucket.

Checkpoint promotion should require both aggregate success preservation and
non-regression on clearance-margin buckets.
