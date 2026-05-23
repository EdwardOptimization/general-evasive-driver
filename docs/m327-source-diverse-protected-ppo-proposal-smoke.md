# M327 Source-Diverse Protected PPO Proposal Smoke

M327 runs a smoke PPO proposal from the M325 public-gate base, then applies
exact repair and proof gates. M327 is not a promotion milestone. Actor inputs
are unchanged.

## Base And Raw PPO

Base:

```text
runs/m316_exact_repair_from_raw_s40_seed10096/candidate_checkpoint.pt
```

Config:

```text
configs/ppo_m327_source_diverse_protected_proposal_smoke.json
```

Raw PPO run:

```text
runs/ppo_m327_source_diverse_protected_proposal_smoke_seed5236
```

Raw PPO metrics:

| Metric | Value |
| --- | ---: |
| rollout_return_mean | 64.478414 |
| reward_mean | 0.955173 |
| train termination_rate | 0.222222 |
| eval return_mean | 70.944443 |
| eval termination_rate | 0.000000 |

The raw PPO checkpoint is proposal-only and is not promotable.

## Exact Repair

Exact repair run:

```text
runs/m327_exact_repair_from_raw_s40_seed10097
```

Candidate:

```text
runs/m327_exact_repair_from_raw_s40_seed10097/candidate_checkpoint.pt
```

Exact objective retention versus M325:

| Objective | Delta |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000104308 |
| Exact M270 source-balanced outcome | -0.000066042 |

Both exact objectives pass no-regression.

## Source-Diverse Protected Gate

Run dir:

```text
runs/m327_source_diverse_protected_gate
```

All three M320 source-diverse protected replay gates pass.

| Replay gate | Rows | Baseline drops | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| current_repaired_surface | 17 | 17 | 17 | +0.000193834 | +0.000084878 | true |
| m317_continuity_surface | 17 | 17 | 17 | +0.000388630 | +0.000165122 | true |
| m314_continuity_surface | 17 | 17 | 17 | +0.000389153 | +0.000165322 | true |

## Old 9944 Diagnostic

Old protected key `9944|perturbed|28|28` remains a diagnostic.

| Policy | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m263_a005 | true | 0.199909 | 0.099300 | 0.100609 |
| m325_base | false | 0.207388 | 0.110406 | 0.096982 |
| m327_repaired | false | 0.213944 | 0.121291 | 0.092653 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

The candidate fails the historical singleton normal-margin window, but retains:

```text
margin_gap = 0.09265276126719213
M324 diagnostic floor = 0.09
```

Classification:

```text
single_key_window_saturation
```

## First Replay Gates

Both first replay gates pass versus M325.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M170 | 17 | 17 / 17 | +0.000220939 | +0.000030599 | true |
| M267/M264 | 17 | 17 / 17 | +0.000193843 | +0.000084890 | true |

## Interpretation

M327 is a positive proof-gated smoke PPO result:

```text
M325 base
  -> smoke PPO proposal
  -> exact M297/M270 repair
  -> source-diverse protected bundle
  -> old-key singleton-window audit
  -> first replay gates
```

This shows PPO can still propose useful movement after M325, and the new
source-diverse protected policy avoids returning to old `9944` alpha clipping.
Because M327 is not a promotion milestone, the repaired candidate must go
through a separate full public gate.

## Decision

Admit:

```text
m328-full-public-gate-for-m327-source-diverse-repaired
```

Decision:

```text
admit_m328_full_public_gate_for_m327_source_diverse_repaired
```
