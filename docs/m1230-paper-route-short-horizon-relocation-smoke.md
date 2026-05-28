# M1230 Paper-Route Short-Horizon Relocation Smoke

## Summary

M1230 reruns the M1227 bounded relocation grid at the M1222-compatible
short horizon (`max_continuation_steps=12`) selected by M1229.

Decision:

```text
short_horizon_relocation_partial_source_collapsed_audit_required
```

M1230 finds a real short-horizon materialization signal, but it is not
source-diverse enough to pass the proof gate:

```text
accepted_wrong_rows: 80
accepted_wrong_success_drop_fraction: 1.0
accepted_wrong_physical_pairs: 34
accepted_wrong_left_steps: 2
accepted_wrong_targets: 1
accepted_wrong_normal_margin_buckets: 1
accepted_wrong_margin_gap_mean: 0.0022355233
accepted_wrong_margin_gap_max: 0.0024104702
passed: false
```

No training, PPO, promotion, private holdout, profile tuning, or actor-input
change occurs in M1230.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_balanced_boundary_relocation_surface \
  --checkpoint-policy l3_s111602=runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --env-config configs/paper_route_corrected_profiles/m1207_l3_online_gru.json \
  --outcome-csv runs/m1226_terminal_boundary_candidate_export/candidate_outcomes.csv \
  --delay-steps 10 \
  --max-continuation-steps 12 \
  --target-normal-margins 0.0005,0.001,0.002,0.003,0.005,0.010 \
  --half-width-inflations 0,0.10 \
  --body-longitudinal-offsets=-2,0,2 \
  --body-lateral-offsets=-0.25,0,0.25 \
  --min-normal-margin 0.0 \
  --max-normal-margin 0.20 \
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
  --run-dir runs/m1230_short_horizon_relocation_smoke
```

## Source And Candidate Gates

Source budget:

```text
candidate_wrong_history_rows:       274
eligible_physical_pairs:            110
eligible_left_steps:                  5
eligible_targets:                     2
eligible_source_obstacle_buckets:     5
source_budget_ready: true
```

Candidate selection:

```text
selected_rows:             100
selected_physical_pairs:   100
selected_left_steps:         5
selected_targets:            2
decision: source_balanced_candidates_ready
```

The run entered relocation replay under corrected source and candidate gates.

## Outcome

M1230 produced accepted wrong-history rows:

```text
boundary_relocation_rows:       7200
balanced_exportable_rows:         80
accepted_wrong_rows:              80
accepted_wrong_success_drop:   1.000
normal_margin range: [0.0006900428, 0.0021887161]
variant_margin range: [-0.0017204274, -0.0000528075]
margin_gap range: [0.0007428503, 0.0024104702]
```

Every accepted row is a true success drop:

```text
normal_success: true
variant_success: false
normal_terminal_reason: continuation_limit
variant_terminal_reason: collision
```

This is the first positive materialization signal in the terminal-boundary
branch.

## Why It Does Not Pass

The accepted surface collapses on key source-diversity dimensions:

```text
accepted_wrong_rows:                  80 / threshold 80     pass
accepted_wrong_physical_pairs:        34 / threshold 10     pass
accepted_wrong_left_steps:             2 / threshold 5      fail
accepted_wrong_checkpoints:            1 / threshold 3      fail
accepted_wrong_targets:                1 / threshold 2      fail
accepted_wrong_normal_margin_buckets:  1 / threshold 2      fail
accepted_wrong_success_drop_fraction:  1.0 / threshold 1.0  pass
max_rows_per_physical_pair_fraction:   0.0375 / threshold 0.05 pass
```

Accepted rows are all:

```text
target: unavoidable
left_step: 18 or 21
checkpoint: l3_s111602
normal_margin_bucket: one bucket
```

Therefore M1230 is not a proof pass and must not be promoted into a training
corpus or paper claim without audit.

## Interpretation

M1230 supports a narrow claim:

```text
M1226 action-divergent candidates can be materialized into short-horizon
wrong-history success drops under obstacle relocation.
```

M1230 does not support:

```text
source-diverse causal-history proof
long-horizon evasive-driver performance
recurrent belief
self-identification
promotion
training readiness
```

## Next

M1231 should audit the partial positive surface before any new run.

The audit should decide whether to:

```text
1. expand source diversity around accepted short-horizon rows;
2. mine/focus additional targets and left steps;
3. route to fault/extreme scenario source generation;
4. stop the terminal-boundary branch if the signal remains narrow.
```

Do not train from M1230 yet. The correct next step is a process audit, not PPO.
