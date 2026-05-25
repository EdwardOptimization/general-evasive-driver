# M902 V4 Pair-Delta Raw Scaling Challenge Generalization Design

## Purpose

M902 designs a second public scenario-family benchmark for the raw scaling
candidates after M900 produced a margin-only fresh pass on the m121-style
distribution.

M902 is design-only:

```text
no benchmark execution
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Challenge Families

M903 should run:

```text
near-threshold robust:
  configs/m451_challenge_near_threshold_robust_zero_relvel.json

late high-energy robust:
  configs/m451_challenge_late_high_energy_robust_zero_relvel.json
```

These configs are public workflow diagnostics, not private holdouts.

## Candidate Set

Policies:

```text
heuristic
random
m568_base
m886_a010
m891_a010
m886_raw
m891_raw
```

Checkpoints:

```text
m568_base: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
m886_a010: runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/alpha_0_1.pt
m891_a010: runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/alpha_0_1.pt
m886_raw:  runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt
m891_raw:  runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
```

## Benchmark Setup

Runs:

```text
runs/m903_raw_scaling_challenge_near_threshold_seed9905
runs/m903_raw_scaling_challenge_late_high_energy_seed9906
runs/m903_raw_scaling_challenge_seed_delta
```

Episodes:

```text
128 per challenge family
```

Seeds:

```text
near-threshold: 9905
late high-energy: 9906
```

## Acceptance Rules

For each raw candidate, compared with `m568_base`:

```text
success_rate_delta >= -0.01 on each challenge family
termination_rate_delta <= +0.01 on each challenge family
clearance_margin_mean_delta >= 0.0 on each challenge family
combined_clearance_margin_mean_delta >= +0.001 across both families
```

Interpretation:

```text
success/termination non-regression is mandatory;
clearance must not flip negative on either challenge family;
combined positive clearance is required to preserve the M900 margin signal;
return remains diagnostic unless it collapses severely.
```

Alpha `0.1` candidates are low-effect references. If raw candidates do not
exceed alpha `0.1` clearance on the challenge families, raw scaling is likely
not worth integrating.

## Seed-Delta Audit

After both benchmarks, run seed-delta audit:

```text
baseline: m568_base
candidates: m886_a010, m891_a010, m886_raw, m891_raw
```

Use it to inspect:

```text
success flips;
regressions;
clearance/margin deltas;
return deltas;
scenario-family-specific failures.
```

Do not use the same challenge benchmark as a private holdout for tuning.

## Failure Routing

```text
sampling failure
  -> challenge config sampling audit

raw success or termination regression
  -> behavior-regression audit

raw clearance negative on either challenge family
  -> raw scaling generalization failure audit

raw margin positive but no success flips
  -> branch synthesis before public-base integration design

raw success or strong seed-level improvement
  -> public-base integration design, still no direct promotion
```

## Decision

Decision:

```text
raw_scaling_challenge_generalization_design_admit_m903
```

Next:

```text
m903-v4-pair-delta-raw-scaling-challenge-generalization-benchmark
```

M903 may execute the no-training challenge benchmark and seed-delta audit. It
must not train, run PPO, mutate actor inputs, or promote a checkpoint.
