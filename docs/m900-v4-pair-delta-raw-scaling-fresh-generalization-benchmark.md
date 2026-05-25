# M900 V4 Pair-Delta Raw Scaling Fresh Generalization Benchmark

## Purpose

M900 executes the no-training fresh/generalization benchmark designed in M899.

M900 does not train, run PPO, or promote a checkpoint.

## Benchmark Runs

Environment:

```text
configs/m121_human_view_zero_obstacle_relvel.json
```

Runs:

```text
runs/m900_raw_scaling_fresh_generalization_seed9705
runs/m900_raw_scaling_fresh_generalization_seed9706
```

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

Episodes:

```text
256 per benchmark seed
```

## Policy Summary

Seed `9705`:

```text
policy     success  termination  clearance_mean  return_mean
m568_base  0.761719 0.238281     1.477508        67.273908
m886_a010  0.761719 0.238281     1.477930        67.270261
m891_a010  0.761719 0.238281     1.477932        67.270253
m886_raw   0.761719 0.238281     1.480724        67.241156
m891_raw   0.761719 0.238281     1.480737        67.241081
```

Seed `9706`:

```text
policy     success  termination  clearance_mean  return_mean
m568_base  0.761719 0.238281     1.483118        67.364947
m886_a010  0.761719 0.238281     1.483543        67.361282
m891_a010  0.761719 0.238281     1.483544        67.361274
m886_raw   0.761719 0.238281     1.486355        67.332006
m891_raw   0.761719 0.238281     1.486368        67.331931
```

Raw candidate deltas versus M568:

```text
candidate  success_delta  termination_delta  clearance_delta  return_delta
m886_raw   0.0            0.0                +0.003236        -0.032942
m891_raw   0.0            0.0                +0.003250        -0.033017
```

Alpha `0.1` candidate deltas versus M568:

```text
candidate  success_delta  termination_delta  clearance_delta  return_delta
m886_a010  0.0            0.0                +0.000425        -0.003666
m891_a010  0.0            0.0                +0.000426        -0.003674
```

M900 meets the pre-registered fresh benchmark thresholds:

```text
raw success_rate_delta >= -0.005: pass
raw termination_rate_delta <= +0.005: pass
raw clearance_margin_mean_delta >= +0.002: pass
```

## Seed-Delta Audit

Run:

```text
runs/m900_raw_scaling_fresh_generalization_seed_delta
```

Summary:

```text
candidate  pairs  success_delta_rate  improved_seeds  regressed_seeds  clearance_delta_mean  clearance_delta_median
m886_a010  256    0.0                 0               0                +0.000425             +0.000285
m891_a010  256    0.0                 0               0                +0.000426             +0.000286
m886_raw   256    0.0                 0               0                +0.003236             +0.002807
m891_raw   256    0.0                 0               0                +0.003250             +0.002815
```

Return deltas:

```text
m886_raw: -0.032942 mean, -0.015308 median
m891_raw: -0.033017 mean, -0.015347 median
```

## Interpretation

M900 supports a fresh public diagnostic claim:

```text
Raw objective-only candidates retain success and termination on the M900 fresh
benchmark and show a repeatable clearance-margin lift above the pre-registered
+0.002 threshold.
```

It does not support:

```text
success-rate improvement;
collision-rate improvement;
private holdout generalization;
public-base integration;
PPO admission;
checkpoint promotion.
```

The useful signal is clearance/margin movement, not success flips:

```text
improved_success_seeds: 0
regressed_success_seeds: 0
```

## Decision

Decision:

```text
raw_scaling_fresh_generalization_benchmark_pass_margin_only
```

Next:

```text
m901-v4-pair-delta-raw-scaling-fresh-result-audit
```

M901 should decide whether margin-only fresh movement is enough to justify
public-base integration design, another fresh scenario family, or richer
pair-delta corpus construction. It must not promote or run PPO directly.
