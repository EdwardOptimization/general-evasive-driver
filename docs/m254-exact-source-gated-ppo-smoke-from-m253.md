# M254 Exact-Source-Gated PPO Smoke From M253

M254 runs one 1024-step PPO smoke from the M253 public-gate base. The run
completes, but exact source-aware gating rejects every interpolated candidate
because the protected-key source regresses. No proof or behavior gates were run
after the exact source failure.

Actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt
```

PPO config:

```text
configs/ppo_m248_source_balanced_from_m239_smoke.json
```

Raw PPO run:

```text
runs/ppo_m254_exact_source_from_m253_seed5225
```

Interpolation sweep:

```text
runs/m254_m253_to_raw_interpolation
```

Exact source evaluation:

```text
runs/m254_source_aware_exact_m232_eval
```

## PPO Smoke

Training completed at `1024` steps.

| Step | Rollout return mean | Reward mean | Episodes | Rollout termination | Built-in eval termination | M223 source loss | Protected-key source loss | Baseline anchor loss | Snippet anchor loss | Trajectory anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 69.709 | 1.045 | 10 | 0.2000 | 0.0000 | 0.211783 | 0.0356445 | 0.0000287 | 0.0000000217 | 0.000000199 |

The run is mechanically valid and even improves the small built-in eval
termination rate. That is not sufficient for promotion.

## Exact Source Gate

Aggregate M232 loss decreases for every alpha:

| Policy | Alpha | Exact M232 | Delta vs M253 |
| --- | ---: | ---: | ---: |
| m253_a0_00008 | 0 | 0.244635209 | 0 |
| m254_a100 | 0.10 | 0.244632825 | -0.000002384 |
| m254_a250 | 0.25 | 0.244629264 | -0.000005946 |
| m254_a500 | 0.50 | 0.244623333 | -0.000011876 |
| m254_a750 | 0.75 | 0.244617581 | -0.000017628 |
| m254_a1000 | 1.00 | 0.244611919 | -0.000023291 |

But this aggregate improvement comes from M223 while the protected-key source
moves in the wrong direction.

| Policy | Alpha | M223 source delta | Protected-key source delta |
| --- | ---: | ---: | ---: |
| m254_a100 | 0.10 | -0.000003291 | +0.000000878 |
| m254_a250 | 0.25 | -0.000008198 | +0.000002206 |
| m254_a500 | 0.50 | -0.000016321 | +0.000004431 |
| m254_a750 | 0.75 | -0.000024351 | +0.000006708 |
| m254_a1000 | 1.00 | -0.000032320 | +0.000009006 |

The pre-registered exact source gate required:

```text
M223 source delta < 0
aggregate M232 delta <= +1e-8
protected_key source delta <= +1e-8
```

No alpha satisfies the protected-key condition.

## Interpretation

M253's source calibration lowered the starting protected-key loss, but it did
not change the sign of the PPO update direction on that source. The same
failure mode from M248 persists:

- PPO makes M223 and aggregate M232 look better;
- protected-key source moves against the lexicographic proof gate;
- broad rollout/eval improvement is therefore not admissible.

## Decision

Reject M254. Keep M253 as the current public-gate base:

```text
runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt
```

Failure taxonomy:

```text
objective_overfit
proof_washout
promotion_gate_failure
```

Next step:

```text
m255-m254-protected-source-regression-audit
```
