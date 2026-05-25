# M901 V4 Pair-Delta Raw Scaling Fresh Result Audit

## Purpose

M901 audits M900 and chooses the next route after the raw objective-only
candidates passed a fresh public diagnostic benchmark.

M901 is audit-only:

```text
no benchmark execution
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## M900 Summary

M900 benchmarked:

```text
configs/m121_human_view_zero_obstacle_relvel.json
seeds: 9705, 9706
episodes: 256 per seed
```

Raw candidate aggregate deltas versus M568:

```text
candidate  success_delta  termination_delta  clearance_delta  return_delta
m886_raw   0.0            0.0                +0.003236        -0.032942
m891_raw   0.0            0.0                +0.003250        -0.033017
```

Alpha `0.1` candidate aggregate deltas versus M568:

```text
candidate  success_delta  termination_delta  clearance_delta  return_delta
m886_a010  0.0            0.0                +0.000425        -0.003666
m891_a010  0.0            0.0                +0.000426        -0.003674
```

Seed-delta audit:

```text
candidate  success_delta_rate  improved_seeds  regressed_seeds  clearance_delta_mean  clearance_delta_median
m886_raw   0.0                 0               0                +0.003236             +0.002807
m891_raw   0.0                 0               0                +0.003250             +0.002815
```

## Supported Claims

M900 supports:

```text
Raw objective-only candidates retain success and termination on a fresh public
diagnostic benchmark.

Raw candidates exceed the pre-registered +0.002 clearance threshold on that
fresh benchmark.

Raw candidates produce roughly 7.6x the alpha_0.1 clearance movement on the
same fresh benchmark.
```

This is useful evidence that M897 was not only a fixed proof-row artifact.

## Unsupported Claims

M900 does not support:

```text
success-rate improvement;
collision-rate improvement;
private holdout generalization;
public-base integration;
PPO safety;
checkpoint promotion.
```

The signal is still margin-only:

```text
improved_success_seeds: 0
regressed_success_seeds: 0
```

## Route Decision

M900 is positive enough to avoid abandoning the objective direction, but not
strong enough for integration or PPO.

The next step should test a different public scenario family before integration:

```text
near-threshold robust challenge
late high-energy robust challenge
```

Reason:

```text
If raw scaling is only a small clearance lift on the same m121-style
distribution, public-base integration is premature.

If it remains non-regressive and margin-positive on challenge families, the
case for integration design becomes stronger.

If it regresses or loses the margin signal, route to richer/fresher pair-delta
corpus construction instead.
```

Decision:

```text
margin_only_fresh_pass_route_to_challenge_generalization_design
```

Next:

```text
m902-v4-pair-delta-raw-scaling-challenge-generalization-design
```

M902 should design a no-training challenge-family benchmark using:

```text
configs/m451_challenge_near_threshold_robust_zero_relvel.json
configs/m451_challenge_late_high_energy_robust_zero_relvel.json
```

M902 must not run the benchmark, train, run PPO, or promote.
