# M903 V4 Pair-Delta Raw Scaling Challenge Generalization Benchmark

## Purpose

M903 executes the no-training robust challenge-family benchmark designed in
M902.

M903 does not train, run PPO, or promote a checkpoint.

## Benchmark Runs

Challenge configs:

```text
configs/m451_challenge_near_threshold_robust_zero_relvel.json
configs/m451_challenge_late_high_energy_robust_zero_relvel.json
```

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

## Near-Threshold Robust

Run:

```text
runs/m903_raw_scaling_challenge_near_threshold_seed9905
```

Summary:

```text
policy     success  termination  clearance_mean  return_mean
m568_base  0.843750 0.156250     1.823597        76.884297
m886_a010  0.843750 0.156250     1.824046        76.880911
m891_a010  0.843750 0.156250     1.824047        76.880901
m886_raw   0.843750 0.156250     1.827294        76.865164
m891_raw   0.843750 0.156250     1.827309        76.865069
```

Raw deltas versus M568:

```text
candidate  success_delta  termination_delta  clearance_delta  return_delta
m886_raw   0.0            0.0                +0.003697        -0.019133
m891_raw   0.0            0.0                +0.003712        -0.019228
```

## Late High-Energy Robust

Run:

```text
runs/m903_raw_scaling_challenge_late_high_energy_seed9906
```

Summary:

```text
policy     success  termination  clearance_mean  return_mean
m568_base  0.781250 0.218750     1.574455        73.837114
m886_a010  0.781250 0.218750     1.574793        73.834420
m891_a010  0.781250 0.218750     1.574794        73.834414
m886_raw   0.781250 0.218750     1.577819        73.810022
m891_raw   0.781250 0.218750     1.577831        73.809963
```

Raw deltas versus M568:

```text
candidate  success_delta  termination_delta  clearance_delta  return_delta
m886_raw   0.0            0.0                +0.003364        -0.027092
m891_raw   0.0            0.0                +0.003376        -0.027151
```

## Seed-Delta Audit

Run:

```text
runs/m903_raw_scaling_challenge_seed_delta
```

Summary:

```text
candidate  success_delta_rate  improved_seeds  regressed_seeds  clearance_delta_mean  clearance_delta_median
m886_a010  0.0                 0               0                +0.000338             +0.000246
m891_a010  0.0                 0               0                +0.000339             +0.000246
m886_raw   0.0                 0               0                +0.003364             +0.002453
m891_raw   0.0                 0               0                +0.003375             +0.002461
```

The seed-delta audit reports no success flips:

```text
improved_seeds: 0
regressed_seeds: 0
```

## Gate Result

M903 passes the pre-registered challenge-family gates:

```text
raw success_rate_delta >= -0.01 on each family: pass
raw termination_rate_delta <= +0.01 on each family: pass
raw clearance_margin_mean_delta >= 0.0 on each family: pass
raw combined clearance_margin_mean_delta >= +0.001: pass
```

## Interpretation

M903 strengthens the M900 result:

```text
The raw objective-only candidates preserve success/termination and retain a
positive margin signal on two robust challenge families.
```

The signal is still margin-only:

```text
success_delta_rate: 0.0
improved_success_seeds: 0
regressed_success_seeds: 0
```

Unsupported claims remain:

```text
success improvement;
private holdout generalization;
PPO safety;
public-base integration;
checkpoint promotion.
```

## Decision

Decision:

```text
raw_scaling_challenge_generalization_benchmark_pass_margin_only
```

Next:

```text
m904-v4-pair-delta-objective-effect-size-branch-synthesis
```

M904 should synthesize M895-M903 before deciding whether to move toward
public-base integration design, richer corpus construction, another scenario
family, or stopping this branch.
