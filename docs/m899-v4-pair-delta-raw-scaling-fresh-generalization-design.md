# M899 V4 Pair-Delta Raw Scaling Fresh Generalization Design

## Purpose

M899 designs a no-training fresh/generalization benchmark for the raw scaling
candidates that passed M897 public proof gates.

M899 is design-only:

```text
no benchmark execution
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Candidate Set

M900 should compare:

```text
m568_base
m886_a010
m891_a010
m886_raw
m891_raw
heuristic
random
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

Environment config:

```text
configs/m121_human_view_zero_obstacle_relvel.json
```

Fresh benchmark seeds:

```text
9705
9706
```

Episodes per seed:

```text
256
```

Run dirs:

```text
runs/m900_raw_scaling_fresh_generalization_seed9705
runs/m900_raw_scaling_fresh_generalization_seed9706
runs/m900_raw_scaling_fresh_generalization_seed_delta
```

These seeds are public workflow diagnostics, not private holdout evidence.

## Acceptance Rules

For each raw candidate, compared with `m568_base` over the combined fresh
benchmark:

```text
success_rate_delta >= -0.005
termination_rate_delta <= +0.005
clearance_margin_mean_delta >= +0.002
```

Interpretation:

```text
success/termination retention is required;
clearance delta is the effect-size gate;
return is diagnostic, not first-class success unless it collapses severely.
```

Alpha `0.1` candidates are included as low-effect references:

```text
If raw candidates do not clearly exceed alpha_0.1 on clearance movement, raw
scaling has weak fresh-distribution value.
```

Seed-delta audit:

```text
Run seed_delta_audit after benchmarks.
Mine m886_a010, m891_a010, m886_raw, and m891_raw versus m568_base.
Use it to find seed-level success, collision, clearance, and return deltas.
Do not use it to tune the same benchmark as a private holdout.
```

## Failure Routing

```text
scenario sampling failure
  -> sampling/config audit

raw success or termination regression
  -> behavior-regression audit

raw clearance delta < +0.002 and no seed-level benefit
  -> richer/fresher pair-delta corpus design

raw improves clearance but not success
  -> fresh-result audit before any scaling or integration

raw improves success or meaningful seed-level outcomes
  -> public-base integration design, still no direct promotion
```

## Decision

Decision:

```text
raw_scaling_fresh_generalization_design_admit_m900
```

Next:

```text
m900-v4-pair-delta-raw-scaling-fresh-generalization-benchmark
```

M900 may execute the no-training fresh benchmark and seed-delta audit. It must
not train, run PPO, mutate actor inputs, or promote a checkpoint.
