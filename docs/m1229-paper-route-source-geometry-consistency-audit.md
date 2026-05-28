# M1229 Paper-Route Source-Geometry Consistency Audit

## Summary

M1229 runs exact source-geometry replay with no obstacle offsets and no
half-width inflation at two horizons.

Decision:

```text
source_geometry_consistency_horizon_mismatch_route_to_short_horizon_relocation
```

Result:

```text
short horizon, 12 steps:
  normal_success: 100 / 100
  variant_success: 100 / 100
  normal_collision: 0 / 100
  variant_collision: 0 / 100
  accepted_wrong_rows: 0
  margin_gap max: 0.0023704993

long horizon, 60 steps:
  normal_success: 0 / 100
  variant_success: 0 / 100
  normal_collision: 100 / 100
  variant_collision: 100 / 100
  accepted_wrong_rows: 0
```

No training, PPO, promotion, private holdout, profile tuning, or actor-input
change occurs in M1229.

## Commands

Short horizon:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_balanced_boundary_relocation_surface \
  --checkpoint-policy l3_s111602=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --env-config configs/paper_route_corrected_profiles/m1207_l3_online_gru.json \
  --outcome-csv runs/m1226_terminal_boundary_candidate_export/candidate_outcomes.csv \
  --delay-steps 10 \
  --max-continuation-steps 12 \
  --target-normal-margins 999 \
  --half-width-inflations 0 \
  --body-longitudinal-offsets=0 \
  --body-lateral-offsets=0 \
  --min-normal-margin 0.0 \
  --max-normal-margin 1.0 \
  --min-margin-gap 0.010 \
  --report-variants wrong_matched_history \
  --max-candidates 120 \
  --max-candidates-per-physical-pair 1 \
  --max-candidates-per-checkpoint-target 64 \
  --target-min-physical-pairs 40 \
  --target-min-left-steps 5 \
  --target-min-targets 2 \
  --max-rows-per-pair-fraction 0.05 \
  --min-eligible-physical-pairs 40 \
  --max-candidate-pair-fraction 0.05 \
  --device cpu \
  --run-dir runs/m1229_source_geometry_consistency_short
```

Long horizon:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_balanced_boundary_relocation_surface \
  --checkpoint-policy l3_s111602=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --env-config configs/paper_route_corrected_profiles/m1207_l3_online_gru.json \
  --outcome-csv runs/m1226_terminal_boundary_candidate_export/candidate_outcomes.csv \
  --delay-steps 10 \
  --max-continuation-steps 60 \
  --target-normal-margins 999 \
  --half-width-inflations 0 \
  --body-longitudinal-offsets=0 \
  --body-lateral-offsets=0 \
  --min-normal-margin 0.0 \
  --max-normal-margin 1.0 \
  --min-margin-gap 0.010 \
  --report-variants wrong_matched_history \
  --max-candidates 120 \
  --max-candidates-per-physical-pair 1 \
  --max-candidates-per-checkpoint-target 64 \
  --target-min-physical-pairs 40 \
  --target-min-left-steps 5 \
  --target-min-targets 2 \
  --max-rows-per-pair-fraction 0.05 \
  --min-eligible-physical-pairs 40 \
  --max-candidate-pair-fraction 0.05 \
  --device cpu \
  --run-dir runs/m1229_source_geometry_consistency_long
```

## Short-Horizon Result

Artifacts:

```text
runs/m1229_source_geometry_consistency_short/summary.json
runs/m1229_source_geometry_consistency_short/boundary_relocation_rows.csv
```

Exact source geometry at `12` steps reproduces normal-success source behavior:

```text
rows: 100
normal_success: 100
variant_success: 100
normal_collision: 0
variant_collision: 0
normal_terminal_reason: continuation_limit
variant_terminal_reason: continuation_limit
normal_margin range: [0.0492284368, 0.9461493859]
variant_margin range: [0.0495690485, 0.9455451925]
margin_gap range: [-0.0029554275, 0.0023704993]
accepted_wrong_rows: 0
```

Interpretation:

```text
source replay is consistent at the M1222 short continuation horizon, but exact
source geometry alone does not create wrong-history outcome degradation.
```

## Long-Horizon Result

Artifacts:

```text
runs/m1229_source_geometry_consistency_long/summary.json
runs/m1229_source_geometry_consistency_long/boundary_relocation_rows.csv
```

Exact source geometry at `60` steps collides for all selected rows:

```text
rows: 100
normal_success: 0
variant_success: 0
normal_collision: 100
variant_collision: 100
normal_terminal_reason: collision
variant_terminal_reason: collision
normal_margin range: [-0.1945879451, -0.0080074171]
variant_margin range: [-0.1941138672, -0.0033634946]
margin_gap range: [-0.0062997352, 0.0037195477]
accepted_wrong_rows: 0
```

Interpretation:

```text
M1227's all-collision result is primarily a horizon mismatch. M1222 candidates
are short-horizon source-safe, not long-horizon source-safe.
```

## Scientific Interpretation

M1229 does not produce causal-history proof rows. It clarifies the failure:

```text
not source schema mismatch
not missing source diversity
not enough for self-identification

yes horizon mismatch
yes short-horizon source consistency
yes relocation materialization must be horizon-scoped
```

This means future terminal-boundary materialization runs must explicitly state
whether they are testing:

```text
short-horizon action divergence materialization
long-horizon evasive-driving success
```

Those are different evidence levels.

## Next

M1230 should run a bounded short-horizon relocation materialization smoke:

```text
same source-balanced M1226 candidates
same bounded relocation grid as M1227
max_continuation_steps = 12
claim scope = short-horizon materialization only
```

If M1230 finds accepted rows, the result may support short-horizon
causal-history materialization but not long-horizon evasive-driver performance.
If M1230 is negative, terminal-boundary materialization should pivot to stronger
source distributions, such as explicit fault/extreme scenarios, rather than
continuing to tune the same grid.
