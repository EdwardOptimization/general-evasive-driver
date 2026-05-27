# M1093 V4 Public Base Source-Balanced Compact Corpus Conversion Design

## Purpose

M1093 designs the next step after M1092 passed the source-balanced
wrong-history boundary export. The intended next step was compact
objective/replay corpus conversion before any future PPO.

This milestone is design-only. It does not train, run PPO, promote a
checkpoint, use private holdout, or change actor inputs.

## Input Surface

Use:

```text
runs/m1092_source_balanced_coverage_expansion_seed109200/balanced_accepted_wrong_history_rows.csv
```

M1092 surface:

```text
accepted_wrong_rows: 146
physical_pairs: 18
left_steps: 9
checkpoints: 4
targets: 3
normal_margin_buckets_at_0.005m: 4
success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.1369863014
control_accepted_wrong_rows: 0
```

This is a passed proof surface at aggregate source-balanced level.

## Direct Conversion Audit

The previous M1058 pattern converts one compact corpus per checkpoint label
using `boundary_outcome_corpus_objective`. That tool filters rows by
`checkpoint_label`, so the aggregate M1092 surface must also be compact enough
within each checkpoint label.

Preflight with `max_rows_per_physical_pair=2`:

```text
proof_current: rows 8, physical_pairs 4, targets 2
short61049: rows 13, physical_pairs 8, targets 2
short61050: rows 10, physical_pairs 8, targets 3
short61051: rows 20, physical_pairs 13, targets 3
```

Preflight with no physical-pair cap:

```text
proof_current: rows 16, physical_pairs 4, targets 2
short61049: rows 17, physical_pairs 8, targets 2
short61050: rows 13, physical_pairs 8, targets 3
short61051: rows 29, physical_pairs 13, targets 3
```

Therefore a direct M1058-style conversion is not ready. The aggregate surface
passes because source diversity exists across the four-checkpoint family, but
some per-checkpoint compact corpora would be sparse. In particular,
`proof_current` cannot reach `10` physical pairs under any cap because the
source rows only cover `4` physical pairs for that label.

## Design Decision

Do not route directly to objective/replay conversion.

The next milestone should first run a compactability audit that answers:

```text
1. Should conversion be per-checkpoint, family-aggregate, or family-intersection?
2. Which minimum row/pair thresholds are scientifically defensible for each mode?
3. Can a compact corpus preserve the M1092 source-diverse proof without hiding
   per-checkpoint sparsity?
4. Which replay sanity pairs should be mandatory before any future PPO?
```

The audit must not weaken the M1092 proof gate. It should only decide the
correct conversion contract.

## Candidate Conversion Modes

### Mode A: Per-Checkpoint Corpora

This matches M1058 and is easiest to compare with old conversion runs.

Problem:

```text
proof_current and short61050 are sparse by physical pairs.
```

Use only if the audit defines lower per-checkpoint minimums and clearly states
that this is a diagnostic corpus, not a robust per-policy conversion.

### Mode B: Family-Aggregate Corpus

Use all accepted rows across checkpoint labels and keep `checkpoint_label` as
metadata. This preserves M1092 aggregate source diversity.

Problem:

```text
existing boundary_outcome_corpus_objective is checkpoint-filtered, so this may
require a new conversion path or explicit audit before implementation.
```

### Mode C: Family-Intersection Corpus

Filter rows that retain normal success and wrong-history failure across the
current family, similar to M1061.

Problem:

```text
requires replay sanity before conversion and may shrink the corpus.
```

This is probably the cleanest route if future PPO should depend on the corpus.

## Required M1094 Audit

M1094 should be a no-training, no-PPO audit over the M1092 accepted rows.

Minimum output:

```text
per_checkpoint_compactability.csv
aggregate_compactability.csv
recommended_conversion_mode.json
summary.json
```

For each mode and cap, report:

```text
rows
physical_pairs
left_steps
targets
checkpoints
max_rows_per_physical_pair_fraction
normal_margin_buckets
success_drop_fraction
```

Recommended caps to audit:

```text
max_rows_per_physical_pair: 0, 2, 3, 4, 5
min_margin_gap: 0.0, 0.002, 0.005
```

The audit should pick one conversion mode and pre-register the actual
conversion run only after the mode is clear.

## Self-ID Claim Level

M1093 does not change the claim level. It preserves the M1092 claim:

```text
level2_history_encoded_reactive proof-surface evidence
```

No level-3 anticipatory self-identification claim is allowed because this
surface still uses matched-current snapshots and current ego response.

## Decision

```text
source_balanced_compact_conversion_design_route_to_compactability_audit
```

Next:

```text
m1094-v4-public-base-source-balanced-compactability-audit
```
