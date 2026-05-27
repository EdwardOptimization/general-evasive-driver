# M1106 V4 Public Base Family-Aggregate Conversion Synthesis

## Purpose

M1106 synthesizes the `family_aggregate_boundary_conversion` branch before any
corpus build or objective-sanity run.

This milestone is process-only. It does not train actor weights, run PPO, run
replay, build a corpus, run objective sanity, mine rows, promote a checkpoint,
use private holdout, or change actor inputs.

## Evidence Summary

M1096 defined an export-only family-aggregate contract because the existing
boundary-outcome objective intentionally avoids mixed hidden-state spaces.

M1097 implemented that export and preserved the M1092 source-balanced surface:

```text
rows: 146
physical_pairs: 18
left_steps: 9
source checkpoints: 4
targets: 3
success_drop_fraction: 1.0
max_pair_fraction: 0.136986
```

M1098 and M1099 added and ran source-aware replay sanity. Source-policy
source-row replay passed for all `146` rows:

```text
normal successes: 146
wrong-history successes: 0
success drops: 146
```

M1100 audited cross-family replay. It found that direct mixed-source objective
optimization over all `146` rows is unsafe, but the all-policy intersection is
still broad:

```text
all-policy pass rows: 133
physical_pairs: 14
source labels: 4
targets: 3
left_steps: 9
```

M1101 and M1102 designed and implemented the deterministic family-intersection
selector. It kept `133` rows and dropped the `13` cross-family failure rows,
with diversity still passing.

M1103 and M1104 designed and implemented `proof_current` target-policy
materialization. It rewrote objective fields from `proof_current` replay rows
while preserving source metadata. Validation passed:

```text
rows: 133
normal successes: 133
wrong-history successes: 0
success drops: 133
finite objective rows: 133
physical_pairs: 14
source labels: 4
targets: 3
left_steps: 9
```

M1105 designed the next corpus/objective sanity run and separated raw proof rows
from the deduplicated objective input. The existing corpus builder is expected
to deduplicate to `68` unique boundary rows.

## Supported Claims

The branch supports these claims:

```text
1. The M1092 source-balanced proof surface can be converted into a raw-retained
   family aggregate export without losing source metadata.
2. Source-policy replay validates the original proof relation for all 146 rows.
3. Cross-family replay identifies source-specific rows that should not be mixed
   directly into an objective.
4. A deterministic all-policy selector preserves 133 rows with acceptable
   source, target, and physical-pair diversity.
5. The selected rows can be materialized for one target policy, proof_current,
   without mixing source hidden-state spaces or source-row objective labels.
```

## Unsupported Or Falsified Claims

The branch does not support these claims:

```text
1. It does not show driver improvement.
2. It does not promote a checkpoint.
3. It does not show PPO readiness.
4. It does not show private-holdout or paper-level generalization.
5. It does not prove level3 anticipatory self-identification.
6. It does not yet show that the materialized rows produce a learnable
   auxiliary objective.
```

Direct mixed-source objective conversion was rejected. The supported route is
target-policy materialization followed by single-checkpoint corpus/objective
sanity.

## Failure Taxonomy Summary

The key failure class was not proof washout. It was conversion and sampling
structure:

```text
scenario_sampling_failure:
  per-checkpoint compact conversion was sparse;
  compact-dedup aggregate lost too many rows;
  cross-family failures were concentrated in source-specific boundary rows.

metric_artifact risk:
  mitigated by separating source-policy proof pass from cross-family report
  failures and by refusing direct mixed-source objective conversion.

none:
  M1097 export, M1099 source-policy replay, M1102 selector, and M1104
  materialization passed their registered gates.
```

## Public-Gate Overfit Risk

The branch uses public proof rows and source-family replay artifacts. This is
appropriate for proof-surface hardening, but it cannot be interpreted as
private generalization or driver capability.

Overfit controls added by the branch:

```text
source-balanced export
source-policy replay sanity
cross-family replay audit
all-policy intersection selector
target-policy materialization
no mixed-source objective NPZ
branch synthesis before objective sanity
```

Remaining risk:

```text
the next objective sanity may still learn a public proof-surface auxiliary
signal that does not transfer to broader scenario distributions.
```

That risk must be handled later by fresh-surface, generalization, and
promotion gates. It is outside the claim scope of this conversion branch.

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

Close:

```text
family_aggregate_boundary_conversion
```

Open:

```text
materialized_objective_corpus_sanity
```

The next branch should run the pre-registered M1105 objective-corpus sanity
experiment. Passing that experiment may admit objective audit or actor-update
design; it still must not promote a checkpoint or claim driver improvement.

## Decision

```text
family_aggregate_conversion_synthesis_open_materialized_objective_corpus_sanity
```

Next:

```text
m1107-v4-public-base-materialized-objective-corpus-run
```

## Validation

Research validation:

```text
make research-validate
```

Result:

```text
research validation passed
```
