# M129 Combined Outcome Objective Sanity

M128 produced a deduplicated accepted-only outcome-intervention corpus. M129
tests whether the M124 calibrated checkpoint can fit that combined corpus while
retaining behavior.

This is an objective-sanity milestone, not PPO admission and not driver success.

## Setup

Initial checkpoint:

```text
runs/m124_calib_s120_lr5e5_anchor10_seed9821/optimized_checkpoint.pt
```

Snippet corpus:

```text
runs/m128_combined_outcome_snippet_corpus/outcome_intervention_snippets.npz
```

Recipe:

```text
steps=120
learning_rate=0.00005
batch_size=64
logprob_margin=0.05
train_scope=actor_coupling
action_anchor_coef=10.0
action_anchor_checkpoint=M124 9821
```

## Objective Result

| Run | Before loss | After loss | Improvement | After anchor MSE |
| --- | ---: | ---: | ---: | ---: |
| seed 9830 | 0.281314 | 0.171088 | 0.110226 | 0.002512 |
| seed 9831 | 0.281314 | 0.175752 | 0.105563 | 0.002225 |
| seed 9832 | 0.281314 | 0.178909 | 0.102405 | 0.002170 |

The objective signal is repeatable across all three seeds. This is much larger
than the M124 objective-sanity loss movement on the earlier M122 corpus, but it
is still a fixed-corpus result.

## Behavior Gate

All behavior runs use:

```text
configs/m121_human_view_zero_obstacle_relvel.json
episodes=80
```

Seed `9500`:

| Policy | Success | Termination | Return mean | Clearance mean | Clearance min |
| --- | ---: | ---: | ---: | ---: | ---: |
| M124 9821 | 0.8625 | 0.1375 | 65.630692 | 1.859754 | -0.125811 |
| M129 9830 | 0.8625 | 0.1375 | 65.838307 | 1.853314 | -0.186491 |
| M129 9831 | 0.8625 | 0.1375 | 65.850526 | 1.853911 | -0.182432 |
| M129 9832 | 0.8625 | 0.1375 | 65.825534 | 1.853518 | -0.177848 |
| M129 9830 reset | 0.8375 | 0.1625 | 63.298946 | 1.858460 | -0.169918 |
| M129 9830 zero-current | 0.8000 | 0.2000 | 60.656437 | 1.873888 | -0.147615 |
| M129 9830 zero-all | 0.8000 | 0.2000 | 60.656437 | 1.873888 | -0.147615 |
| M129 9830 no-action | 0.8625 | 0.1375 | 65.380989 | 1.858619 | -0.161616 |

Seed `9501`:

| Policy | Success | Termination | Return mean | Clearance mean | Clearance min |
| --- | ---: | ---: | ---: | ---: | ---: |
| M124 9821 | 0.8625 | 0.1375 | 66.151242 | 1.878626 | -0.125811 |
| M129 9830 | 0.8625 | 0.1375 | 66.355927 | 1.872366 | -0.186491 |
| M129 9830 reset | 0.8375 | 0.1625 | 63.859740 | 1.875612 | -0.169918 |
| M129 9830 zero-current | 0.8000 | 0.2000 | 61.334170 | 1.891103 | -0.147615 |
| M129 9830 zero-all | 0.8000 | 0.2000 | 61.334170 | 1.891103 | -0.147615 |
| M129 9830 no-action | 0.8625 | 0.1375 | 65.903916 | 1.878688 | -0.161616 |

Behavior retention holds on both seeds. Zero-response degradation also repeats.
No-action history remains neutral, which is a known limitation from M125.

## Decision

M129 is a positive objective-sanity result and is admitted to a formal repeat
gate.

What passed:

- M128 objective loss improves repeatably across seeds `9830-9832`;
- action-anchor MSE remains small;
- normal behavior success matches M124 on seeds `9500` and `9501`;
- zero-current and zero-all response ablations still reduce success to
  `0.8000`;
- reset hidden reduces success to `0.8375`.

What did not pass:

- no-action history remains neutral;
- source-side coverage is still perturbed-only through M128;
- the result has not yet shown fresh strict outcome-proof-surface repeat after
  the objective update;
- therefore this is not PPO admission.

Next step: M130 should formally repeat behavior and wrong-history
outcome-proof-surface gates before any PPO continuation.
