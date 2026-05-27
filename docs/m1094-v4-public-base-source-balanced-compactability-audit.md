# M1094 V4 Public Base Source-Balanced Compactability Audit

## Purpose

M1094 implements and runs a compactability audit for the passed M1092
source-balanced wrong-history boundary surface before objective/replay
conversion.

This milestone does not train, run PPO, promote a checkpoint, use private
holdout, or change actor inputs.

## Implementation

Added:

```text
src/autodrift/source_balanced_compactability_audit.py
tests/test_source_balanced_compactability_audit.py
```

The audit reads:

```text
runs/m1092_source_balanced_coverage_expansion_seed109200/balanced_accepted_wrong_history_rows.csv
```

and writes:

```text
runs/m1094_source_balanced_compactability_audit/per_checkpoint_compactability.csv
runs/m1094_source_balanced_compactability_audit/aggregate_compactability.csv
runs/m1094_source_balanced_compactability_audit/recommended_conversion_mode.json
runs/m1094_source_balanced_compactability_audit/summary.json
```

Audited settings:

```text
max_rows_per_physical_pair: 0, 2, 3, 4, 5
min_margin_gap: 0.0, 0.002, 0.005
margin_bucket_width: 0.005
```

Modes:

```text
per_checkpoint / compact_dedup
family_aggregate / compact_dedup
family_aggregate / raw_retained
family_intersection / replay_required_proxy
```

The `family_intersection` rows are explicitly marked as replay-required proxy
rows. M1094 does not run family replay.

## Audit Results

The input surface is unchanged from M1092:

```text
accepted_wrong_rows: 146
physical_pairs: 18
left_steps: 9
checkpoints: 4
targets: 3
success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.1369863014
```

Per-checkpoint compact-dedup conversion remains sparse. At
`min_margin_gap=0.0` and no physical-pair cap:

```text
proof_current: rows 16, physical_pairs 4, targets 2
short61049:    rows 17, physical_pairs 8, targets 2
short61050:    rows 13, physical_pairs 8, targets 3
short61051:    rows 29, physical_pairs 13, targets 3
```

Only `short61051` can meet the `>=20 rows`, `>=10 physical_pairs`, and
`>=2 targets` compact corpus threshold. `proof_current` cannot meet the
physical-pair threshold under any audited cap because its source rows cover
only four physical pairs.

Family aggregate compact-dedup also remains row-limited:

```text
min_margin_gap=0.0, cap=0:
  rows: 75
  physical_pairs: 18
  checkpoints: 4
  targets: 3
  threshold_pass: false
```

The raw-retained family aggregate preserves the passed M1092 surface:

```text
min_margin_gap=0.0, cap=0:
  rows: 146
  physical_pairs: 18
  left_steps: 9
  checkpoints: 4
  targets: 3
  normal_margin_buckets: 4
  success_drop_fraction: 1.0
  max_rows_per_physical_pair_fraction: 0.1369863014
  threshold_pass: true
```

## Recommendation

```text
recommended_mode: family_aggregate
recommended_selection_kind: raw_retained
decision: source_balanced_compactability_recommend_family_aggregate_conversion_design
ready_for_existing_conversion_path: false
requires_new_conversion_path: true
requires_replay_before_objective_conversion: true
```

The existing M1058-style per-checkpoint compact conversion path should not be
used for M1092. It would hide per-checkpoint sparsity and overstate
compact-corpus readiness.

The next branch should design a family-aggregate conversion contract that
keeps checkpoint labels and raw retained rows explicit, then adds replay sanity
before any objective optimization or PPO.

## Self-ID Claim Level

M1094 does not upgrade the evidence claim:

```text
level2_history_encoded_reactive
```

The audit only checks whether a passed matched-current wrong-history proof
surface can be converted. It does not add a new temporal evidence window,
warm-up phase, hidden-condition change, or anticipatory self-identification
test.

## Validation

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_source_balanced_compactability_audit.py
```

Result:

```text
5 passed
```

Harness tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_research_validate.py \
  tests/test_research_manifest.py \
  tests/test_research_cycle.py \
  tests/test_source_balanced_compactability_audit.py
```

Result:

```text
38 passed
```

Research validation:

```text
make research-validate
```

Result:

```text
research validation passed
process_v5_from_priority=10850
```

Git hook:

```text
.git/hooks/pre-commit
```

Result:

```text
19 passed
```

## Decision

```text
source_balanced_compactability_recommend_family_aggregate_conversion_design
```

Next:

```text
m1095-v4-public-base-source-balanced-boundary-tooling-synthesis
```

The branch has reached the workflow synthesis cadence. M1095 should synthesize
M1085-M1094 and decide whether to close `source_balanced_boundary_tooling` and
open a family-aggregate conversion branch.
