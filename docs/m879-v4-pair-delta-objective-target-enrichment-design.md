# M879 V4 Pair-Delta Objective Target Enrichment Design

## Purpose

M879 designs the no-training enrichment step required after M878 found that
M877's deduplicated accepted rows are structurally cleaner but still not
objective-ready.

The design question is:

```text
How should deduplicated pair-delta rows be joined back to sequence rollout rows
so future objective design has concrete action targets and rejected/accepted
action evidence?
```

M879 is design-only:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
no final loss design
```

## M878 Blocker

M877 fixed the duplicate-axis artifact and produced purpose-specific public
splits:

```text
dedup_rows: 247
new_dedup_rows: 13
objective_train_rows: 124
objective_train_new_rows: 8
objective_eval_rows: 22
objective_eval_new_rows: 2
new_signature_holdout_rows: 3
new_duplicate_factor_after: 1.0
```

But the accepted-row artifacts do not carry the sequence action targets needed
by a future objective:

```text
normal_first_steer / throttle / brake
right_first_steer / throttle / brake
first_override_steer / throttle / brake
requested_delta_l2_per_step
effective_delta_l2_max
clip_fraction_mean
terminal_reason
steps
```

So objective design must stay blocked until an enrichment artifact restores
these fields.

## Sequence Sources

M880 should not assume all rows can be recovered from M873 sequence rows.

M877 has two evidence origins:

```text
existing_m867_or_m870: 234 rows
new_m873: 13 rows
```

The correct sequence sources are:

```text
existing_m867_or_m870 rows:
  runs/m867_v4_generated_boundary_pair_delta_refresh/pair_delta_sequence_rows.csv

new_m873 rows:
  runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/pair_delta_sequence_rows.csv
```

Observed join sanity from live artifacts:

```text
M877 dedup rows: 247
unique sequence matches using the proposed primary key: 247
missing matches: 0
multi matches: 0
```

This check is not a training result. It only shows that the enrichment
implementation has a well-defined deterministic join route.

## Join Key

M880 should use a primary exact row identity key that is present in both M877
deduped rows and sequence-row sources:

```text
pair_id
left_candidate_id
right_candidate_id
left_source_group_id
right_source_group_id
left_seed
right_seed
left_step
right_step
direction
hold_steps
epsilon_l2
normal_margin
sequence_margin
```

Rationale:

```text
dedup_signature intentionally excludes pair_id and retarget_axis so duplicate
axis labels collapse, but each canonical M877 row still retains a concrete
source rollout row. The enrichment join should recover that canonical rollout's
action targets, not re-expand duplicate axis labels into samples.
```

M880 may also record a diagnostic `sequence_source_path` and `sequence_source`
field:

```text
m867_sequence
m873_boundary_preserving_sequence
```

## Fallback Rules

If the primary key fails, M880 should not silently guess.

Allowed fallback:

```text
try a dedup_signature-equivalent match that ignores pair_id and retarget_axis
only if all matched sequence rows have identical action target fields within
numeric tolerance.
```

Failure route:

```text
if no match exists, or if multiple matches disagree on target actions, stop and
classify as metric_artifact / lineage_invalid risk; route to exact replay
regeneration instead of objective design.
```

## Required Enriched Fields

M880 should preserve all M877 fields and append the sequence-derived fields:

```text
normal_first_steer
normal_first_throttle
normal_first_brake
right_first_steer
right_first_throttle
right_first_brake
first_override_steer
first_override_throttle
first_override_brake
requested_delta_l2_per_step
effective_delta_l2_max
clip_fraction_mean
first_action_l2_vs_normal
prefix_l2_mean_vs_normal
prefix_l2_max_vs_normal
terminal_reason
steps
sequence_source
sequence_source_path
enrichment_join_key
enrichment_match_count
```

M877 already carries several useful outcome fields, such as
`effective_delta_l2_mean`, `effective_sequence_l2`, `clip_fraction_max`, and
`severe_clip_steps`; M880 should keep them and verify consistency against the
sequence source when the fields exist in both inputs.

## Target Semantics

M880 should not design the final objective loss, but it should name target
semantics for the later objective-readiness audit:

```text
normal_action:
  action emitted by the current base policy under the normal/correct history.

right_action:
  first action from the paired/right hidden condition.

override_action:
  first action of the bounded pair-delta intervention sequence.

accepted_class:
  pair_delta_improvement or pair_delta_degradation, preserved from M877.
```

Future objective design can then decide whether to treat
`first_override_action` as a preferred recovery target, a rejected trajectory
target, or a pairwise contrast. M880 should only provide the data.

## Output Artifacts

M880 should write:

```text
src/autodrift/v4_pair_delta_objective_target_enrichment.py
tests/test_v4_pair_delta_objective_target_enrichment.py
runs/m880_v4_pair_delta_objective_target_enrichment/summary.json
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_dedup_pair_delta_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_train_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_eval_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_source_holdout_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_new_signature_holdout_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/join_summary.csv
runs/m880_v4_pair_delta_objective_target_enrichment/gate_summary.csv
docs/m880-v4-pair-delta-objective-target-enrichment-implementation.md
```

## Gates

Primary gates:

```text
dedup_rows_enriched == 247
objective_train_rows_enriched == 124
objective_eval_rows_enriched == 22
source_holdout_rows_enriched == 98
new_signature_holdout_rows_enriched == 3
missing_join_count == 0
ambiguous_join_count == 0
target_action_fields_present == true
split_labels_preserved == true
duplicate_metadata_preserved == true
new_source_holdout_available == false
caveat_78055_recorded == true
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
```

Classification:

```text
objective_overfit:
  reduced if action targets are restored without duplicate re-expansion.

metric_artifact:
  fail if the join is ambiguous or target fields are inferred from labels.

scenario_sampling_failure:
  still present because new source holdout is unavailable and 78055 remains a
  caveat.

contract_violation:
  fail if actor inputs are changed or privileged fields are introduced into
  actor observations.
```

## Decision

Decision:

```text
pair_delta_objective_target_enrichment_design_admit_m880
```

Next:

```text
m880-v4-pair-delta-objective-target-enrichment-implementation
```

Objective training, actor update, PPO, and checkpoint promotion remain blocked
until the enriched corpus is implemented and audited.
