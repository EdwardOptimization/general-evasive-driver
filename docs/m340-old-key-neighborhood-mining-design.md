# M340 Old-Key Neighborhood Mining Design

M340 designs the next no-PPO mining stage after M339 showed that existing
corpora cannot replace the singleton `9944` gap floor. It does not train,
repair, promote, lower any threshold, or change actor inputs.

## Problem From M339

M339 found:

```text
broad pool rows: 195
broad max source-family dominance: 0.087179
compact severity rows: 26
compact max source-family dominance: 0.461538
old-key 9944 endpoint gap delta: -0.02479489280545555
M267/M264 success-drop regressions: 2
M133 accepted-case regressions: 1
```

The broad pool is large enough for inspection, but the compact severity draft is
too dominated by M133 historical keys and duplicated M183 rows. Therefore it is
diagnostic evidence, not a valid replacement gate.

The next stage must mine a wider old-key neighborhood instead of reusing the
same fixed proof rows.

## Design Principle

M341 should mine reference cases from the current public base first, then
evaluate candidate checkpoints against those cases.

Do not mine rows by directly optimizing for the M335 endpoint failure. The
reference corpus should be selected from deployable closed-loop behavior under
the current base:

```text
reference policy: M333 base / current-family base behavior
comparison policies:
  M335 alpha 0.0075 promoted candidate
  M335 repaired endpoint
```

This preserves the research question:

```text
Does the endpoint broadly erode old wrong-history gap evidence,
or only move a saturated singleton?
```

## Seed Blocks

Use fresh and source-separated seed blocks instead of only M133 seeds:

| Block | Seed | Episodes | Role |
| --- | ---: | ---: | --- |
| A | 9860 | 40 | pre-M133 neighborhood |
| B | 9900 | 40 | M133 overlap diagnostic |
| C | 9940 | 40 | old-key local neighborhood |
| D | 9980 | 40 | post-M133 neighborhood |
| E | 10020 | 40 | fresh current-family neighborhood |

M133 all-key rows and `9944` stay diagnostics. They are not sufficient by
themselves for source-diverse replacement.

## Relocation Grid

Use a wider but still old-key-focused relocation grid:

```text
snapshot distances: 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5
lateral offsets: -1.2, -1.0, -0.8
half widths: 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4
```

Keep the M133-style handling-limit randomization:

```text
env_config: configs/m121_human_view_zero_obstacle_relvel.json
nominal mu: 0.85, 1.15
perturbed mu: 0.25, 0.35
probe: steer_brake, steer 0.25, brake 0.20, period 20
obstacle reveal distance: 16.0
max continuation steps: 40
```

Use relaxed current-family mining bounds so old-key-like rows are not excluded
just because the current base has larger margins than the old M133 reference:

```text
min margin gap: 0.002
min normal margin: -0.005
max normal margin: 0.30
require normal success: true
max visible distance: 0.75
max response distance: 0.35
max context distance: 0.05
```

## M341 Command Shape

M341 should run `snapshot_bank_relocation` on the current base for each seed
block. Example for block A:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.snapshot_bank_relocation \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --checkpoint runs/m332_m328_to_m330_gap_bounded_interpolation/checkpoints/alpha_0_45.pt \
  --episodes 40 \
  --seed 9860 \
  --device cpu \
  --nominal-friction-mu-range 0.85 1.15 \
  --perturbed-friction-mu-range 0.25 0.35 \
  --obstacle-perception-reveal-distance 16.0 \
  --bank-obstacle-distance-range 5.0 12.0 \
  --bank-stride-steps 3 \
  --bank-max-snapshots 40 \
  --bank-max-pairs-per-seed 4 \
  --snapshot-relocation-distances 9.5,10.0,10.5,11.0,11.5,12.0,12.5 \
  --snapshot-relocation-lateral-offsets -1.2,-1.0,-0.8 \
  --snapshot-relocation-half-widths 0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4 \
  --min-probe-steps 10 \
  --max-probe-steps 180 \
  --min-hidden-updates-after-friction 2 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.35 \
  --max-context-distance 0.05 \
  --min-margin-gap 0.002 \
  --min-normal-margin -0.005 \
  --max-normal-margin 0.30 \
  --max-continuation-steps 40 \
  --probe-strategy steer_brake \
  --probe-steer-amplitude 0.25 \
  --probe-brake-level 0.20 \
  --probe-period-steps 20 \
  --outcome-export-min-margin-gap 0.002 \
  --outcome-export-boundary-margin-scale 0.20 \
  --export-only-accepted-outcomes \
  --top-k 400 \
  --max-selected-per-physical-pair 2 \
  --max-selected-per-seed 4 \
  --run-dir runs/m341_old_key_neighborhood_block_a_seed9860
```

After mining, M341 should replay the mined cases with:

```text
m333_base
m335_a0075
m335_repaired
```

The replay can use `critical_key_replay_guard` with the M341 mined
`outcome_sensitive_snippets.csv` files as reference cases, or a new wrapper if
multiple seed-block reference CSVs need to be evaluated together.

## Aggregation

M341 should export:

```text
runs/m341_old_key_neighborhood_mining/old_key_neighborhood_candidate_pool.csv
runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv
runs/m341_old_key_neighborhood_mining/summary.json
```

The aggregator should report:

```text
rows
unique seed blocks
unique physical pairs or keys
unique source steps
unique target buckets
max seed-block dominance
max physical-pair dominance
mean / median / p10 / min endpoint gap delta
endpoint accepted-case regressions
endpoint success-drop regressions
selected-alpha regressions
9944 diagnostic row
M133 all-key diagnostic rows
```

## Acceptance Targets

Broad pool target:

```text
rows >= 80
seed blocks >= 4
physical pairs or keys >= 20
source steps >= 8
target buckets >= 4
max seed-block dominance <= 0.25
```

Compact corpus target:

```text
rows: 20 to 40
seed blocks >= 4
physical pairs or keys >= 15
source steps >= 6
target buckets >= 4
max seed-block dominance <= 0.25
max physical-pair dominance <= 0.15
```

M335 repaired endpoint should be classified repair-needed if either:

```text
compact endpoint gap p10 <= -0.001
or compact endpoint gap min <= -0.01
or endpoint accepted/success-drop regressions >= 2
```

M335 alpha 0.0075 should pass only if:

```text
selected alpha accepted/success-drop regressions == 0
selected alpha gap p10 >= -0.0005
selected alpha gap min >= -0.002
```

These are proposal thresholds for M341. They must be reported in M341 before
any gate replacement is used for PPO acceptance.

## Holdout Discipline

M341 is public diagnostic mining. It is allowed to guide gate design, but it is
not a private holdout and should not be used as paper-grade unbiased evidence.

If M341 is used to tune a replacement gate, a later private or frozen holdout
must be created before making paper-level claims.

## Decision

Admit:

```text
m341-old-key-neighborhood-mining-run
```

M341 should execute the no-PPO mining and aggregation plan. Until M341 passes
the diversity targets, the singleton `9944` floor remains active and no further
PPO continuation should run.
