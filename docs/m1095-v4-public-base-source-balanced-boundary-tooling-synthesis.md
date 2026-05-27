# M1095 V4 Public Base Source-Balanced Boundary Tooling Synthesis

## Purpose

M1095 synthesizes the `source_balanced_boundary_tooling` branch after M1094
completed the compactability audit. This is a process milestone only.

It does not train, run PPO, run replay, mine rows, promote a checkpoint, use
private holdout, or change actor inputs.

## Evidence Summary

M1085 identified the source-diversity failure in M1083 and designed explicit
source-budget and source-balanced boundary tooling rather than post-filtering a
six-pair accepted set.

M1086 implemented the tooling:

```text
source budget
source-balanced candidate selection
balanced export marking
existing-artifact smoke CLI
```

M1088 confirmed that the pre-boundary source budget was ready:

```text
eligible physical pairs: 371
selected physical pairs: 370
```

but the old M1083 boundary export remained limited to six accepted physical
pairs. That falsified post-filtering as a solution.

M1089 and M1090 moved source balancing before relocation replay. M1090 added
the full source-balanced relocation runner and process-v5 self-identification
evidence discipline.

M1091 ran the first full source-balanced relocation replay. It fixed the source
diversity issue but missed the accepted-row threshold:

```text
accepted_wrong_rows: 76 / 80 required
physical_pairs: 18
left_steps: 9
checkpoints: 4
targets: 3
success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.157895
```

M1092 expanded candidate coverage from `512` to `1024` and passed the
source-balanced boundary export gate:

```text
accepted_wrong_rows: 146
physical_pairs: 18
left_steps: 9
checkpoints: 4
targets: 3
normal_margin_buckets: 4
success_drop_fraction: 1.0
max_rows_per_physical_pair_fraction: 0.136986
control_accepted_wrong_rows: 0
```

M1093 audited direct conversion and found that M1058-style per-checkpoint
conversion is sparse even though the aggregate surface is robust.

M1094 implemented the compactability audit and selected the next conversion
contract:

```text
per-checkpoint compact-dedup:
  proof_current: 16 rows / 4 pairs
  short61049:    17 rows / 8 pairs
  short61050:    13 rows / 8 pairs
  short61051:    29 rows / 13 pairs

family aggregate compact-dedup:
  75 rows / 18 pairs

family aggregate raw-retained:
  146 rows / 18 pairs
```

The audit recommends:

```text
recommended_mode: family_aggregate
recommended_selection_kind: raw_retained
ready_for_existing_conversion_path: false
requires_new_conversion_path: true
requires_replay_before_objective_conversion: true
```

## Supported Claims

Source balancing before relocation replay works. The project moved from a
six-physical-pair bottleneck in M1083 to a passing source-balanced surface in
M1092.

The remaining issue is no longer source-diverse boundary discovery. M1092 has
enough aggregate rows, physical pairs, left steps, checkpoints, targets, and
normal-margin buckets under unchanged robustness thresholds.

The existing per-checkpoint compact conversion path is not suitable for the
M1092 surface. It would hide the fact that `proof_current`, `short61049`, and
`short61050` are sparse as standalone compact corpora.

Family-aggregate raw-retained conversion is the only audited route that
preserves the full M1092 proof surface.

## Falsified Claims

Post-filtering an already source-limited boundary export is enough. M1088
showed the source budget was ready before boundary export, but the existing
boundary artifact still had only six accepted physical pairs.

The first source-balanced replay was sufficient as-is. M1091 missed the
accepted-row threshold by four rows, so candidate coverage had to be expanded.

M1058-style per-checkpoint conversion can be reused unchanged. M1093 and M1094
showed per-checkpoint compact-dedup conversion is sparse for the M1092 surface.

Compact-dedup family aggregate is enough. M1094 found only `75` compact-dedup
rows against the `80` aggregate threshold.

## Failure Taxonomy Summary

```text
M1085: none
  design-only; source-balanced tooling admitted.

M1086: none
  implementation-only; focused tests passed.

M1087: none
  process rule; staged training discipline added.

M1088: scenario_sampling_failure
  pre-boundary source budget ready, but old artifact remained boundary-limited.

M1089: none
  design-only; runner implementation admitted.

M1090: none
  runner implementation plus self-ID evidence discipline.

M1091: scenario_sampling_failure
  source diversity passed, but accepted-row count was 76/80.

M1092: none
  coverage expansion passed all source-balanced robustness gates.

M1093: scenario_sampling_failure
  direct per-checkpoint compact conversion is sparse.

M1094: none
  audit completed and recommends family-aggregate raw-retained conversion design.
```

No milestone in this branch trained, ran PPO, promoted a checkpoint, changed
actor inputs, or used private holdout.

## Public Gate Overfit Risk

The M1092 surface is a public proof surface mined around the current
public-gate base and short-PPO family. It is useful for proof preservation and
conversion tooling, but it is not private holdout or paper-level generalization
evidence.

The next branch must keep the public-proof scope explicit. A family-aggregate
conversion can become a public gate or objective-sanity tool only after replay
sanity confirms that raw-retained rows still express the intended
normal-history success and wrong-history failure relation under the relevant
candidate policies.

The conversion design must also address hidden-state space mixing. Existing
`boundary_outcome_corpus_objective` deliberately builds one checkpoint corpus
per run. A family-aggregate path must keep `checkpoint_label` and source-policy
metadata explicit rather than silently treating mixed-source hidden states as a
single homogeneous corpus.

## Next Branch Decision

```text
synthesis_decision: promote_to_next_branch
closed_branch: source_balanced_boundary_tooling
opened_branch: family_aggregate_boundary_conversion
```

Next milestone:

```text
m1096-v4-public-base-family-aggregate-conversion-design
```

M1096 should design the new family-aggregate raw-retained conversion contract.
It should not run PPO, train, promote, use private holdout, or claim driver
performance. The design must specify:

```text
1. how raw retained rows keep checkpoint/source metadata;
2. how duplicate geometry across checkpoint labels is represented;
3. how replay sanity is run before objective optimization;
4. how hidden-state/source-policy mixing is handled or avoided;
5. what criteria allow implementation without weakening M1092 thresholds.
```

## Validation

Research validation:

```text
make research-validate
```

Result:

```text
research validation passed
process_v5_from_priority=10850
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
source_balanced_tooling_synthesis_promote_to_family_aggregate_conversion
```
