# M338 Old-Key Gap Distribution Refresh Design

M338 designs the replacement for singleton old-key veto dominance. It does not
run PPO, actor update, or actor-input changes.

## Problem

M337 shows the current blocker is not broad source-diverse proof washout:

```text
M335 repaired endpoint source-diverse gate: 5 / 5 pass
M335 repaired endpoint old 9944 gap: 0.065360 < 0.09
M335 promoted alpha old 9944 gap: 0.090021
```

The fixed `9944|perturbed|28|28` scalar floor protects a real old proof row,
but it now dominates the trust region. It clips a 4096-step PPO repair direction
to alpha `0.0075` even though broader source-diverse proof remains intact.

The fix should not be to lower the floor ad hoc. The fix should be to replace
single-row veto dominance with a pre-registered source-diverse old-key/gap
distribution gate.

## Design Goal

Build a distributional gate that answers:

```text
Does this candidate broadly erode old wrong-history gap evidence,
or only move one saturated singleton row?
```

The old `9944` row remains in diagnostics. It should not be deleted or hidden.
But after the distributional gate exists, a single `9944` scalar should not be
the only reason useful PPO directions are forced into micro-alpha promotion.

## Candidate Pool

M339 should mine old-key/gap candidates from existing replay and reference
surfaces, not from a new PPO run:

```text
runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv
runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv
runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv
runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv
runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv
runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv
```

The mining target is not just "hard rows". It should prioritize rows where:

```text
current base normal history succeeds,
current base wrong history fails or has clearly worse margin,
M335 repaired endpoint erodes the normal-vs-wrong margin gap,
rows are source-diverse rather than duplicates of 9944.
```

## Diversity Requirements

M339 should report both a broad candidate pool and a compact gate corpus.

Minimum broad-pool targets:

```text
accepted rows >= 80
physical pairs or unique seeds >= 10
left/source steps >= 5
obstacle target buckets >= 2
source corpora >= 4
max source dominance <= 25%
```

Minimum compact-gate targets:

```text
rows = 20-40
physical pairs or unique seeds >= 10
left/source steps >= 5
obstacle target buckets >= 2
max source dominance <= 25%
include 9944 as a named diagnostic row
```

If these targets cannot be met, M339 should classify the blocker as
`lineage_invalid` for distributional gating and recommend a wider corpus mining
stage, not PPO continuation.

## Gate Metrics

The existing source-diverse protected gate remains hard:

```text
normal success drop <= 0
success-drop count regression <= 0
normal margin regression <= 0.005
mean margin-gap regression <= 0.001
```

The new old-key/gap distribution gate should report:

```text
mean gap delta
median gap delta
p10 gap delta
min gap delta
fraction of rows with gap regression worse than threshold
fraction of rows with normal-history success loss
source-dominance of regressing rows
```

M338 does not hard-code final numeric distribution thresholds. M339 should
derive and pre-register thresholds from the observed base, M335 endpoint, and
M335 alpha behavior. The required qualitative property is:

```text
M333 / M336 promoted bases pass,
M335 repaired endpoint is classified as unsafe or repair-needed,
M335 alpha 0.0075 passes,
9944 remains visible as a diagnostic row.
```

## Diagnostic Severity

Until M339 validates replacement thresholds, the singleton `9944` floor remains
active for any further PPO proposal.

After M339, the intended policy is:

```text
green:
  distribution gate passes and 9944 is not severely eroded

amber:
  distribution gate passes but 9944 is below its historical singleton floor;
  candidate may proceed to full public gate only with explicit diagnostic note

red:
  distribution gate fails, or 9944 collapses together with distributional gap
  erosion; candidate rejected or repaired before replay
```

The `amber` case is the key change: singleton warning is allowed to be visible
without forcing micro-alpha if distributional evidence says old proof is
retained. M339 must define the actual numeric thresholds before this policy can
be used.

## Next Milestone

M339 should be a no-PPO corpus/gate refresh:

```text
m339-old-key-gap-distribution-corpus-refresh
```

Expected outputs:

```text
runs/m339_old_key_gap_distribution_refresh/old_key_gap_candidate_pool.csv
runs/m339_old_key_gap_distribution_refresh/old_key_gap_compact_corpus.csv
runs/m339_old_key_gap_distribution_refresh/summary.json
docs/m339-old-key-gap-distribution-corpus-refresh.md
```

M339 should not promote a driver and should not run PPO. Its job is to build
the distributional evidence surface needed before the next PPO proposal.

## Decision

Admit:

```text
m339-old-key-gap-distribution-corpus-refresh
```

Decision:

```text
admit_old_key_gap_distribution_corpus_refresh
```
