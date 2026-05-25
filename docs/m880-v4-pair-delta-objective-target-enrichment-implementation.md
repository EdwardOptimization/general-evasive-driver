# M880 V4 Pair-Delta Objective Target Enrichment Implementation

## Purpose

M880 implements the M879 no-training target-action enrichment design.

The implementation question is:

```text
Can every M877 deduplicated pair-delta row recover concrete sequence-derived
action targets without re-expanding duplicate axis labels or changing the actor
contract?
```

M880 is no-training:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Command

```bash
PYTHONPATH=src python -m autodrift.v4_pair_delta_objective_target_enrichment \
  --dedup-rows runs/m877_v4_pair_delta_corpus_dedup_resplit/dedup_pair_delta_rows.csv \
  --objective-train-rows runs/m877_v4_pair_delta_corpus_dedup_resplit/objective_train_public_rows.csv \
  --objective-eval-rows runs/m877_v4_pair_delta_corpus_dedup_resplit/objective_eval_public_rows.csv \
  --source-holdout-rows runs/m877_v4_pair_delta_corpus_dedup_resplit/source_holdout_public_rows.csv \
  --new-signature-holdout-rows runs/m877_v4_pair_delta_corpus_dedup_resplit/new_signature_holdout_public_rows.csv \
  --sequence-rows runs/m867_v4_generated_boundary_pair_delta_refresh/pair_delta_sequence_rows.csv \
  --sequence-rows runs/m873_v4_boundary_preserving_missing_seed_pair_delta_refresh/pair_delta_sequence_rows.csv \
  --run-dir runs/m880_v4_pair_delta_objective_target_enrichment
```

## Implementation

M880 adds:

```text
src/autodrift/v4_pair_delta_objective_target_enrichment.py
tests/test_v4_pair_delta_objective_target_enrichment.py
```

The tool:

```text
1. indexes M867 and M873 sequence rows by exact identity key;
2. enriches M877 dedup and split rows with sequence action targets;
3. preserves split labels and duplicate metadata;
4. writes join diagnostics and gate summaries;
5. fails if joins are missing or action targets are ambiguous.
```

Sequence source routing:

```text
existing_m867_or_m870 rows -> M867 sequence rows
new_m873 rows              -> M873 boundary-preserving sequence rows
```

## Result

M880 passed the registered gates:

```text
result_class: v4_pair_delta_objective_target_enrichment_pass
dedup_rows_enriched: 247
objective_train_rows_enriched: 124
objective_eval_rows_enriched: 22
source_holdout_rows_enriched: 98
new_signature_holdout_rows_enriched: 3
objective_train_new_rows_enriched: 8
objective_eval_new_rows_enriched: 2
source_holdout_new_rows_enriched: 0
new_signature_holdout_new_rows_enriched: 3
missing_join_count: 0
ambiguous_join_count: 0
target_action_fields_present: true
split_labels_preserved: true
duplicate_metadata_preserved: true
new_source_holdout_available: false
caveat_78055_recorded: true
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Join diagnostics:

```text
join_rows: 494
identity_unique joins: 494
m867_sequence joins: 468
m873_boundary_preserving_sequence joins: 26
target_action_fields_present: 494 / 494
```

The join row count includes the dedup corpus plus all four split files:

```text
247 + 124 + 22 + 98 + 3 = 494
```

## Enriched Artifacts

M880 writes:

```text
runs/m880_v4_pair_delta_objective_target_enrichment/summary.json
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_dedup_pair_delta_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_train_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_eval_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_source_holdout_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/enriched_new_signature_holdout_public_rows.csv
runs/m880_v4_pair_delta_objective_target_enrichment/join_summary.csv
runs/m880_v4_pair_delta_objective_target_enrichment/gate_summary.csv
```

Each enriched row now carries:

```text
normal_first_steer / throttle / brake
right_first_steer / throttle / brake
first_override_steer / throttle / brake
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
enrichment_join_status
```

## Interpretation

Supported claims:

```text
M880 restores concrete action-target fields for every M877 deduplicated and
split row.
M880 does not re-expand duplicate axis labels into independent samples.
M880 preserves the M877 split labels and duplicate metadata.
M880 keeps the 78055 caveat and missing new source holdout visible.
```

Unsupported claims:

```text
M880 admits actor update directly.
M880 admits PPO directly.
M880 proves pair-delta objective usefulness.
M880 proves learned self-identification.
M880 provides source-held-out new M873 evidence.
M880 solves the 78055 caveat.
M880 promotes a checkpoint.
```

Failure taxonomy:

```text
objective_overfit:
  reduced because future objective design can use real actions instead of
  accepted-class labels alone.

metric_artifact:
  reduced because all joins are exact identity_unique and target fields are
  present for all rows.

scenario_sampling_failure:
  still present because source_holdout_new_rows_enriched == 0 and 78055 remains
  absent from new accepted pair-delta rows.

contract_violation:
  not observed; actor observation contract is unchanged.

lineage_invalid:
  not observed; M867 and M873 sequence source routing is explicit.
```

## Decision

Decision:

```text
v4_pair_delta_objective_target_enrichment_pass
```

Next:

```text
m881-v4-enriched-pair-delta-objective-readiness-audit
```

Objective training, actor update, PPO, and checkpoint promotion remain blocked
until the enriched corpus is audited for objective design readiness.
