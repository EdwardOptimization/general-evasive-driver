# M341 Old-Key Neighborhood Mining Run

M341 executes the no-PPO old-key neighborhood mining plan from M340. It does
not train, repair, promote, lower the `9944` floor, or change actor inputs.

## Operational Note

The first command attempt used split range arguments such as:

```text
--nominal-friction-mu-range 0.85 1.15
```

`snapshot_bank_relocation` requires `LOW,HIGH` as one argument. Those attempts
failed in argument parsing before simulation. The commands were corrected to:

```text
--nominal-friction-mu-range 0.85,1.15
--perturbed-friction-mu-range 0.25,0.35
--bank-obstacle-distance-range 5.0,12.0
```

## Mining Runs

Current-base mining policy:

```text
runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt
```

Seed blocks:

| Block | Seed | Run dir | Selected rows | Physical pairs | Selected seeds |
| --- | ---: | --- | ---: | ---: | ---: |
| A | 9860 | `runs/m341_old_key_neighborhood_block_a_seed9860` | 42 | 25 | 12 |
| B | 9900 | `runs/m341_old_key_neighborhood_block_b_seed9900` | 41 | 22 | 11 |
| C | 9940 | `runs/m341_old_key_neighborhood_block_c_seed9940` | 40 | 21 | 14 |
| D | 9980 | `runs/m341_old_key_neighborhood_block_d_seed9980` | 40 | 24 | 13 |
| E | 10020 | `runs/m341_old_key_neighborhood_block_e_seed10020` | 16 | 8 | 6 |

The five blocks produced enough current-base old-key neighborhood rows for the
replacement-gate audit.

## Replay Runs

Comparison policies:

```text
m335_a0075:
  runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt

m335_repaired:
  runs/m335_exact_repair_from_raw_s40_seed10099/candidate_checkpoint.pt
```

Accepted-case replay:

| Block | Cases | M335 alpha accepted | M335 repaired accepted |
| --- | ---: | ---: | ---: |
| A | 42 | 42 | 42 |
| B | 41 | 41 | 37 |
| C | 40 | 40 | 37 |
| D | 40 | 40 | 35 |
| E | 16 | 16 | 13 |
| Total | 179 | 179 | 164 |

Selected alpha retains all mined cases. The repaired endpoint loses `15`
accepted cases across four of five blocks.

## Aggregated Artifacts

```text
runs/m341_old_key_neighborhood_mining/old_key_neighborhood_candidate_pool.csv
runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv
runs/m341_old_key_neighborhood_mining/summary.json
```

The candidate pool contains `179` mined current-family rows plus `12` M133
diagnostic rows. The compact replacement corpus contains `40` severity rows.

## Broad Pool

| Metric | Value |
| --- | ---: |
| Rows | 179 |
| Seed blocks | 5 |
| Physical pairs or keys | 179 |
| Source steps | 32 |
| Target buckets | 76 |
| Max seed-block dominance | 0.234637 |
| Max physical-pair dominance | 0.005587 |
| Passes targets | true |

Broad selected-alpha metrics:

```text
accepted regressions: 0
gap p10: -0.0000037805
gap min: -0.0000489009
```

Broad endpoint metrics:

```text
accepted regressions: 15
gap p10: -0.0005322004
gap min: -0.0506599075
```

## Compact Corpus

| Metric | Value |
| --- | ---: |
| Rows | 40 |
| Seed blocks | 5 |
| Physical pairs or keys | 40 |
| Source steps | 19 |
| Target buckets | 28 |
| Max seed-block dominance | 0.25 |
| Max physical-pair dominance | 0.025 |
| Passes targets | true |

Compact selected-alpha metrics:

```text
accepted regressions: 0
gap p10: -0.0000181822
gap min: -0.0000489009
```

Compact endpoint metrics:

```text
accepted regressions: 15
gap p10: -0.0040711523
gap min: -0.0506599075
```

The compact corpus satisfies the M340 diversity targets:

```text
rows: 20 to 40
seed blocks >= 4
physical pairs or keys >= 15
source steps >= 6
target buckets >= 4
max seed-block dominance <= 0.25
max physical-pair dominance <= 0.15
```

## Gate Interpretation

M335 alpha `0.0075` passes the proposed selected-alpha thresholds:

```text
accepted/success regressions == 0
gap p10 >= -0.0005
gap min >= -0.002
```

M335 repaired endpoint is repair-needed:

```text
accepted regressions: 15 >= 2
compact endpoint gap p10: -0.004071 <= -0.001
compact endpoint gap min: -0.050660 <= -0.01
```

This is the evidence M339 was missing: a source-diverse old-key neighborhood
surface that distinguishes the promoted alpha from the repaired endpoint
without relying on singleton `9944` dominance.

## Decision

M341 produces a valid replacement-gate corpus.

Decision:

```text
admit_m342_old_key_neighborhood_gate_implementation
```

M342 should implement a reusable old-key neighborhood gate around the M341
candidate pool and compact corpus. Until M342 exists and passes validation,
the historical `9944` diagnostic should remain visible and no PPO continuation
should use the new corpus informally.
