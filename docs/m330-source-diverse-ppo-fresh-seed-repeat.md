# M330 Source-Diverse PPO Fresh-Seed Repeat

M330 runs a fresh-seed repeat of the source-diverse protected PPO smoke process
from the M328 public-gate base. The repeat is rejected before first replay
because the old `9944` diagnostic margin gap falls below the pre-registered
floor. Actor inputs are unchanged.

## Raw PPO

Base:

```text
runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt
```

Raw PPO run:

```text
runs/ppo_m330_source_diverse_protected_repeat_seed5237
```

Raw PPO metrics:

| Metric | Value |
| --- | ---: |
| rollout_return_mean | 65.419341 |
| reward_mean | 1.037858 |
| train termination_rate | 0.250000 |
| eval return_mean | 59.686937 |
| eval termination_rate | 0.200000 |

The raw PPO checkpoint is proposal-only and is not promotable.

## Exact Repair

Exact repair run:

```text
runs/m330_exact_repair_from_raw_s40_seed10098
```

Candidate:

```text
runs/m330_exact_repair_from_raw_s40_seed10098/candidate_checkpoint.pt
```

Exact objective retention versus M328:

| Objective | Delta |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000124812 |
| Exact M270 source-balanced outcome | -0.000080585 |

Both exact objectives pass no-regression.

## Source-Diverse Protected Gate

Run dir:

```text
runs/m330_source_diverse_protected_gate
```

All four source-diverse replay gates pass.

| Replay gate | Rows | Baseline drops | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| current_m328_surface | 17 | 17 | 17 | +0.000202621 | +0.000084419 | true |
| m325_continuity_surface | 17 | 17 | 17 | +0.000396455 | +0.000169297 | true |
| m317_continuity_surface | 17 | 17 | 17 | +0.000591253 | +0.000249539 | true |
| m314_continuity_surface | 17 | 17 | 17 | +0.000591776 | +0.000249740 | true |

This means the source-diverse protected proof surfaces are retained.

## Old 9944 Diagnostic

Old protected key `9944|perturbed|28|28` fails the pre-registered margin-gap
floor.

| Policy | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m263_a005 | true | 0.199909 | 0.099300 | 0.100609 |
| m328_base | false | 0.213944 | 0.121291 | 0.092653 |
| m330_repaired | false | 0.219756 | 0.132855 | 0.086901 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

M329 required:

```text
if old-key margin_gap < 0.09, stop before first replay
```

M330 candidate:

```text
margin_gap = 0.08690063195545505
```

Therefore M330 is rejected before first replay.

Failure taxonomy:

```text
protected_key_window_failure
```

## Interpretation

M330 is a mixed negative result:

```text
positive:
  exact M297/M270 improve
  source-diverse protected gates pass 4 / 4

negative:
  old 9944 diagnostic gap falls below the registered floor
  first replay gates are not run
  no promotion is possible
```

This does not prove the source-diverse policy failed, because the source-diverse
bundle remains intact. It does show the fresh-seed repeat is not clean under the
current old-key diagnostic floor.

The next step should audit whether this is a true wrong-history proof erosion
on `9944`, a too-conservative scalar floor, or a candidate-specific old-key
trajectory artifact. Do not lengthen PPO until that audit is complete.

## Decision

Reject:

```text
runs/m330_exact_repair_from_raw_s40_seed10098/candidate_checkpoint.pt
```

Decision:

```text
reject_m330_old_key_gap_floor_failure
```

Next:

```text
m331-m330-old-key-gap-floor-failure-audit
```
