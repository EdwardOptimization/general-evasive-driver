# M754 V4 Sequence-Outcome Corpus Export Design

## Purpose

M754 designs the no-training export step after M753 audited M752 as a clean v4
reset-source sequence-outcome diagnostic positive.

The question is:

```text
Can M752's non-sentinel v4 sequence-outcome rows be preserved as a compact,
auditable corpus without dropping the v4 source metadata and claim-boundary
fields needed for later self-ID objective design?
```

This milestone is design-only:

```text
no actor training
no objective update
no PPO
no checkpoint loading
no checkpoint promotion
no actor-input change
```

## Why Export Before Objective Design

M752 changed the evidence state substantially:

```text
source_candidate_rows: 512
source_reset_rows: 461
source_sentinel_rows: 51
sequence_action_critical_rows: 5429
sequence_outcome_critical_rows: 1213
unique_sequence_outcome_seeds: 27
unique_sequence_outcome_fault_family_pairs: 17
sentinel_false_positive_rows: 0
```

This supports the coverage-mining hypothesis:

```text
Earlier failures to expose closed-loop self-ID may have been partly caused by
insufficient or poorly targeted extreme-scenario mining, not proof that the
actor has no useful command-response history dependence.
```

But M752 is still a public diagnostic wave. Feeding all rows directly into an
objective would risk overfitting the public proof surface. M755 should first
convert the evidence into a deterministic corpus with explicit row roles,
metadata, gates, and claim boundaries.

## Input Artifacts

M755 should read:

```text
runs/m752_v4_reset_source_sequence_intervention/summary.json
runs/m752_v4_reset_source_sequence_intervention/intervention_rollouts.csv
runs/m752_v4_reset_source_sequence_intervention/sequence_critical_rows.csv
runs/m752_v4_reset_source_sequence_intervention/sentinel_rows.csv
configs/extreme_fault_distribution_v4_scenarios.json
docs/m753-v4-reset-source-sequence-intervention-audit.md
```

The exporter should be a deterministic CSV/JSON transform. It must not load a
checkpoint, instantiate an actor, start an optimizer, run PPO, or promote
anything.

## Why The V3 Exporter Is Not Enough

`src/autodrift/v3_sequence_outcome_corpus_export.py` is the right template, but
M752 adds v4-specific claim-boundary fields and source pools:

```text
source_kind
source_pool
claim_boundary_level
pair_id
pairing_rule
reset_action_l2_gap
reset_margin_gap
history_margin_gap
action_l2_gap
match_distance
feature_distance
acceptance_reason
rejection_reason
```

A direct v3 re-export would not make the v4 claim boundary first-class. That
would make later objective documents too easy to overclaim as true per-wheel or
four-wheel failure physics.

M755 should therefore implement a v4-aware exporter. It can reuse the v3 module
structure, but must use v4 names, v4 metadata gates, and v4 result classes.

## Positive Row Selection

Positive sequence-outcome rows are:

```text
sequence_outcome_critical == true
sentinel == false
source_role != sentinel
normal_success == true or normal_margin >= 0
```

Rows that must not be counted as positives:

```text
sentinel rows
source_role == sentinel rows
sequence_action_critical-only rows
temporal_action_critical-only rows
normal-failed rows
rows without matched normal rollout
duplicate positive identity keys
```

Recommended positive identity key:

```text
source_index
seed
step
pair_id
preferred_fault
wrong_fault
fault_family_pair
variant
horizon
```

Registered M752 positive precheck:

```text
positive_rows: 1213
positive_sentinel_rows: 0
unique_positive_seeds: 27
unique_positive_fault_family_pairs: 17
max_positive_seed_dominance: 0.171476
missing_normal_matches: 0
positive_variants:
  reset_hidden_each_step: 169
  zero_command_obs: 1044
positive_horizons:
  H=2: 25
  H=4: 168
  H=6: 455
  H=8: 565
source_kind: v4_reset_source
claim_boundary_level: current_model_or_proxy
```

Because the strongest source is still one public run family, the seed dominance
gate should be:

```text
max_positive_seed_dominance <= 0.20
```

The exported corpus should also report stronger diagnostics by seed, fault
family, fault-family pair, variant, horizon, source kind, source pool, source
role, and claim boundary.

## Contrast Rows

For every positive row, M755 should export one contrast group:

```text
contrast_group_id:
  source_index + horizon + positive variant + pair_id
```

Required group members:

```text
normal:
  same source_index
  same horizon
  variant == normal
  proof_positive == false

positive_intervention:
  the non-sentinel sequence_outcome_critical row
  proof_positive == true
```

Optional hard negatives:

```text
same source_index
same horizon
sequence_action_critical == true
sequence_outcome_critical == false
sentinel == false
source_role != sentinel
normal_success == true or normal_margin >= 0
```

Hard negatives are not proof positives. They should be marked:

```text
contrast_role == hard_negative_action_only
proof_positive == false
```

M752 precheck shows hard negatives are useful but sparse:

```text
action_only_rows: 4216
capped_hard_negative_rows: 1009
positive_rows: 1213
positives_with_no_same_horizon_hard_negative: 338
```

Therefore the core positive corpus gate must not require
`hard_negative_rows >= positive_rows`. M755 should classify sparse hard
negatives separately:

```text
v4_sequence_outcome_corpus_exported:
  positive corpus gates pass and hard_negative_rows >= positive_rows

v4_sequence_outcome_corpus_hard_negative_sparse:
  positive corpus gates pass but hard negatives are sparse
```

Both result classes preserve the positive corpus, but only the first one can be
treated as a complete positive-vs-action-only contrast corpus.

## V4 Metadata Preservation

Every exported positive, contrast, hard-negative, excluded-sentinel, and
rejected row should preserve the M752 rollout fields plus the v4 extra fields:

```text
source_index
source_role
source_pool
source_kind
claim_boundary_level
proposal_id
selected_index
seed
step
preferred_snapshot_id
wrong_snapshot_id
preferred_fault
preferred_fault_family
preferred_fault_severity
wrong_fault
wrong_fault_family
wrong_fault_severity
fault_family_pair
severity_pair
assigned_split
step_bucket
obstacle_distance_bucket
variant
horizon
normal_success
normal_margin
variant_success
variant_margin
margin_gap_from_normal
success_drop_from_normal
first_steer
first_throttle
first_brake
trajectory_l2_mean
trajectory_l2_max
prefix_l2_mean
prefix_l2_max
prefix_compare_steps
terminal_reason
sequence_action_critical
sequence_outcome_critical
temporal_action_critical
temporal_outcome_critical
sentinel
pair_id
pairing_rule
reset_action_l2_gap
reset_margin_gap
history_margin_gap
action_l2_gap
match_distance
feature_distance
acceptance_reason
rejection_reason
```

M755 should enrich rows from
`configs/extreme_fault_distribution_v4_scenarios.json`:

```text
preferred_fidelity_class
wrong_fidelity_class
preferred_fault_params_json
wrong_fault_params_json
```

The summary must include:

```text
fault_config
fault_config_notes
future_only_fault_count
future_only_faults
current_model_fault_count
current_model_proxy_fault_count
claim_boundary_level
```

This prevents later documents from overclaiming true per-wheel failures from
the current proxy data.

## Export Artifacts

M755 should write:

```text
runs/m755_v4_sequence_outcome_corpus_export/summary.json
runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv
runs/m755_v4_sequence_outcome_corpus_export/hard_negative_rows.csv
runs/m755_v4_sequence_outcome_corpus_export/excluded_sentinel_rows.csv
runs/m755_v4_sequence_outcome_corpus_export/rejected_rows.csv
runs/m755_v4_sequence_outcome_corpus_export/source_balance.csv
runs/m755_v4_sequence_outcome_corpus_export/variant_horizon_balance.csv
runs/m755_v4_sequence_outcome_corpus_export/fault_family_balance.csv
docs/m755-v4-sequence-outcome-corpus-export-implementation.md
```

The implementation should add focused tests for:

```text
sentinel positives are excluded
action-only rows are hard negatives, not positives
v4 extra fields are preserved in positive and contrast rows
claim_boundary_level is preserved and summarized
fault fidelity metadata is added from config
duplicate positive identity keys are rejected
artifact failures classify before balance failures
hard-negative sparsity does not invalidate the core positive corpus
no actor training/PPO/checkpoint loading flags are true
```

## Corpus Gates

Core positive gate:

```text
positive_rows >= 1000
positive_sentinel_rows == 0
positive_source_role_sentinel_rows == 0
sentinel_false_positive_rows_exported_as_positive == 0
duplicate_positive_keys == 0
missing_normal_matches == 0
normal_rows == positive_rows
contrast_groups == positive_rows
positive_intervention_rows == positive_rows
unique_positive_seeds >= 24
unique_positive_fault_family_pairs >= 16
max_positive_seed_dominance <= 0.20
```

Variant and horizon gate:

```text
positive_variants include zero_command_obs
positive_horizons include 4, 6, and 8
variant_horizon_balance.csv reports all observed combinations
```

V4 preservation gate:

```text
all exported positive rows include pair_id, source_kind, source_pool,
  and claim_boundary_level
all exported positive rows include reset_action_l2_gap and history_margin_gap
all exported positive rows include preferred_fidelity_class and wrong_fidelity_class
future_only_fault_count is reported in summary
current-model/proxy claim boundary is reported in summary
```

Sentinel gate:

```text
sentinel_input_rows >= 1
excluded_sentinel_rows are written
positive_sentinel_rows == 0
```

Hard-negative reporting gate:

```text
hard_negative_rows are written separately
hard_negative_rows <= 2 * positive_rows
positives_without_hard_negative are counted
hard_negative_complete == (hard_negative_rows >= positive_rows)
```

Hard-negative sparsity should be a result class, not a reason to throw away the
positive corpus.

## Result Classes

M755 should classify the export as one of:

```text
v4_sequence_outcome_corpus_exported:
  core positive, v4 metadata, sentinel, and hard-negative completeness gates pass

v4_sequence_outcome_corpus_hard_negative_sparse:
  core positive, v4 metadata, and sentinel gates pass, but hard negatives are sparse

v4_sequence_outcome_corpus_unbalanced:
  core positive rows exist but seed/fault-family diversity gates fail

v4_sequence_outcome_corpus_sparse:
  fewer than 1000 non-sentinel positive rows remain

v4_sequence_outcome_corpus_artifact:
  sentinel positives, missing normal matches, duplicate keys, or dropped v4 metadata
```

## Registered M755 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v4_sequence_outcome_corpus_export \
  --summary runs/m752_v4_reset_source_sequence_intervention/summary.json \
  --rollouts runs/m752_v4_reset_source_sequence_intervention/intervention_rollouts.csv \
  --sequence-critical-rows runs/m752_v4_reset_source_sequence_intervention/sequence_critical_rows.csv \
  --sentinel-rows runs/m752_v4_reset_source_sequence_intervention/sentinel_rows.csv \
  --fault-config configs/extreme_fault_distribution_v4_scenarios.json \
  --run-dir runs/m755_v4_sequence_outcome_corpus_export \
  --max-hard-negatives-per-positive 2
```

## Allowed Claims

M754 supports:

```text
1. M752 should be preserved as a v4-aware corpus before objective work.
2. The v3 exporter shape is useful but insufficient without v4 claim-boundary fields.
3. Hard-negative sparsity should be reported separately from positive corpus validity.
4. Current-model/proxy faults remain useful for self-ID mining but do not prove
   true per-wheel blowout, split-mu, stuck-caliper, or halfshaft-break physics.
```

M754 does not support:

```text
1. a trained policy improvement claim;
2. PPO continuation;
3. checkpoint promotion;
4. true single-wheel or four-wheel physical-failure claims;
5. objective design before the M755 export is implemented and audited.
```

## Next Step

M755 should implement the v4-aware deterministic exporter and run the registered
export. M756 should audit the resulting corpus before any objective design.
