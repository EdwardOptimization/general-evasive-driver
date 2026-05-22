# M255 M254 Protected-Source Regression Audit

M255 audits the M254 failure before any more PPO. No PPO was run and actor
inputs are unchanged.

## Question

M254 started from a better calibrated public-gate base than M248. The audit asks
whether the protected-key source regression was fixed by that calibration or
whether PPO still moves in a persistent conflicting direction.

## Source Delta Comparison

Both M248 and M254 improve the broad M223 source while regressing the
protected-key source.

| Run | Policy | Alpha | Aggregate delta | M223 source delta | Protected-key source delta | Protected / abs(M223) |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| M248 | m248_a100 | 0.10 | -0.000004046 | -0.000005034 | +0.000000988 | 0.1963 |
| M248 | m248_a500 | 0.50 | -0.000019894 | -0.000024942 | +0.000005048 | 0.2024 |
| M248 | m248_a1000 | 1.00 | -0.000039238 | -0.000049496 | +0.000010258 | 0.2073 |
| M254 | m254_a100 | 0.10 | -0.000002413 | -0.000003291 | +0.000000878 | 0.2667 |
| M254 | m254_a500 | 0.50 | -0.000011890 | -0.000016321 | +0.000004431 | 0.2715 |
| M254 | m254_a1000 | 1.00 | -0.000023314 | -0.000032320 | +0.000009006 | 0.2787 |

M253 calibration reduced the absolute protected-key regression slightly, but it
did not change the sign. The ratio of protected-key regression to M223
improvement is actually higher in M254.

## Train-Metric Check

Both PPO smokes used the same source-balanced recipe:

```text
M223 coef = 0.02
protected-key coef = 0.08
```

Training-time metrics:

| Run | Rollout return | Rollout termination | M223 source loss | Protected-key source loss |
| --- | ---: | ---: | ---: | ---: |
| M248 | 65.914 | 0.3000 | 0.207034 | 0.0356487 |
| M254 | 69.709 | 0.2000 | 0.211783 | 0.0356445 |

The rollout metric improves in M254, but the exact protected-key gate still
fails. This reinforces the harness rule that broad rollout/eval improvement is
not admissible when the protected proof source regresses.

## Diagnosis

This is not a bad-base issue. It is a persistent PPO update-direction conflict:

- source-balanced PPO likes the M223 direction;
- protected-key source still moves against the exact lexicographic gate;
- starting from M253 gives a lower protected-key baseline but does not make PPO
  respect that source.

Increasing duration or repeating the same PPO recipe is not justified.

## Repair Choice

The bounded next repair is a no-PPO post-PPO projection:

1. start from the M254 raw PPO checkpoint;
2. optimize the protected-key source loss in `actor_coupling` scope;
3. anchor preferred snippets against the M253 public-gate base;
4. exact-source-gate the projected checkpoint and, if needed, interpolate back
   toward M253;
5. run proof/behavior gates only after exact source passes.

This tests whether PPO can supply useful broad movement while a projection step
restores the protected source.

## Decision

Admit:

```text
m256-post-ppo-protected-source-projection
```
