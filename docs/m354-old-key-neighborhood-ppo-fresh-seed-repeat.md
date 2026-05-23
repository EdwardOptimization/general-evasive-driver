# M354 Old-Key Neighborhood PPO Fresh-Seed Repeat

M354 runs the fresh-seed short PPO repeat registered by M353. The PPO
checkpoint is proposal-only. M354 does not promote a checkpoint.

## Raw PPO

Base:

```text
runs/m351_m349_to_repaired_old_key_neighborhood_interpolation/checkpoints/alpha_0_0075.pt
```

Config:

```text
configs/ppo_m354_old_key_neighborhood_repeat.json
```

Raw PPO run:

```text
runs/ppo_m354_old_key_neighborhood_repeat_seed5240
```

Raw PPO metrics:

| Metric | Value |
| --- | ---: |
| rollout_return_mean | 78.83 |
| reward_mean | 1.094 |
| eval return_mean | 52.562218 |
| eval termination_rate | 0.200000 |

The raw PPO checkpoint is not promotable.

## Exact Repair

Exact repair run:

```text
runs/m354_exact_repair_from_raw_s40_seed10103
```

Candidate:

```text
runs/m354_exact_repair_from_raw_s40_seed10103/candidate_checkpoint.pt
```

Exact objective retention versus M352:

| Objective | Delta | Pass |
| --- | ---: | --- |
| Exact M297 rejected-history preference | -0.000023007 | true |
| Exact M270 source-balanced outcome | +0.000040591 | false |

M354 fails the exact lexicographic gate. No source-diverse, old-key
neighborhood, replay, or behavior gates are run.

## Interpretation

M354 is a negative fresh-seed repeat. It confirms the raw PPO proposal can run,
and repair improves M297, but the repaired candidate regresses M270. Under the
current gate order this must be rejected before spending compute on replay.

Failure classification:

```text
objective_overfit
```

The next step should audit why the M354 repair trades M270 for M297, instead of
raising PPO length or running downstream gates.

## Decision

Reject:

```text
runs/m354_exact_repair_from_raw_s40_seed10103/candidate_checkpoint.pt
```

Decision:

```text
reject_m354_exact_m270_regression
```

Next:

```text
m355-m354-exact-m270-regression-audit
```
