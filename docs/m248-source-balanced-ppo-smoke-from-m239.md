# M248 Source-Balanced PPO Smoke From M239

M248 runs one 1024-step source-balanced PPO smoke from the M239 public-gate base.
It then stops at the exact source-aware objective gate because every alpha still
regresses the protected-key source component.

Actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
```

Config:

```text
configs/ppo_m248_source_balanced_from_m239_smoke.json
```

Raw PPO checkpoint:

```text
runs/ppo_m248_source_balanced_from_m239_seed5224/checkpoint.pt
```

Interpolation sweep:

```text
runs/m248_m239_to_raw_interpolation
```

Exact source evaluation:

```text
runs/m248_source_aware_exact_m232_eval
```

## Raw PPO Training

| Step | Rollout return mean | Reward mean | Episodes | Rollout termination | Built-in eval termination | M223 source loss | Protected-key source loss | Baseline anchor loss | Snippet anchor loss | Trajectory anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 65.914 | 0.971 | 10 | 0.3000 | 0.2000 | 0.207034 | 0.0356487 | 0.0000199 | 0.000000036 | 0.000000239 |

The training route completed and the source-specific metrics were logged.

## Exact Source-Aware Gate

Aggregate M232 exact loss:

| Policy | Alpha | Exact M232 loss | Delta vs M239 |
| --- | ---: | ---: | ---: |
| m239_a500 | 0.00 | 0.244649454951 | 0.000000000000 |
| m248_a100 | 0.10 | 0.244645401835 | -0.000004053116 |
| m248_a250 | 0.25 | 0.244639411569 | -0.000010043383 |
| m248_a500 | 0.50 | 0.244629561901 | -0.000019893050 |
| m248_a750 | 0.75 | 0.244619786739 | -0.000029668212 |
| m248_a1000 | 1.00 | 0.244610220194 | -0.000039234757 |

Source deltas:

| Policy | Alpha | M223 delta | Protected-key delta |
| --- | ---: | ---: | ---: |
| m248_a100 | 0.10 | -0.000005033935 | 0.000000988085 |
| m248_a250 | 0.25 | -0.000012523957 | 0.000002500899 |
| m248_a500 | 0.50 | -0.000024941800 | 0.000005047827 |
| m248_a750 | 0.75 | -0.000037284507 | 0.000007631578 |
| m248_a1000 | 1.00 | -0.000049495856 | 0.000010258290 |

The pre-registered source gate required:

```text
protected_key delta <= +1e-8
M223 delta < 0
aggregate M232 delta <= +1e-8
```

M248 passes the M223 and aggregate checks, but fails the protected-key source
check for every alpha.

## Proof Gates

Replay, protected-key margin, and behavior gates were not run. The candidate
failed before reaching that stage.

## Diagnosis

M248 is useful negative evidence. Source-balanced loss made the aggregate and
M223 objective direction much stronger than M243, but did not prevent the
protected-key source from drifting in the same wrong direction.

This implies the next repair should not simply run a longer or repeated PPO
with the same source-balanced coefficients. The next step should audit whether
the protected-key source loss can be decreased in isolation and how much PPO
gradient pressure is required to retain it.

Failure taxonomy:

```text
proof_washout
objective_overfit
promotion_gate_failure
```

## Decision

M248 is rejected.

Current public-gate base remains:

```text
runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
```

Next step:

```text
m249-protected-key-source-gradient-audit
```
