# M736 Sequence-Outcome Corpus Export Design

## Purpose

M736 designs a no-training export step after M735 audited M734 as a clean
sequence-level diagnostic positive.

The question is:

```text
Can M734's non-sentinel sequence-outcome rows be preserved as a compact,
auditable corpus for later objective design or repeat validation?
```

This is a design milestone only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Why Export Before Objective Design

M734 changed the evidence state:

```text
M731 accepted outcome rows: 1
M734 sequence outcome rows: 73
M734 non-sentinel outcome rows: 70
M734 outcome seeds: 28
M734 outcome fault-family pairs: 10
```

This is strong enough to preserve as data, but not strong enough to train from
directly. The rows are diagnostic counterfactuals produced by sequence-level
command-response interventions. If they are fed into a loss before filtering,
deduplication, normal matching, and balance checks, the next branch can easily
turn into public-row overfitting.

So M737 should first produce a corpus with explicit row roles and audit fields.
Only after that corpus is implemented and audited should the project decide
whether to design a sequence-preference objective, a repeat validation wave, or
a broader extreme-fault distribution.

## Input Artifacts

Primary inputs:

```text
runs/m734_sequence_command_response_intervention/summary.json
runs/m734_sequence_command_response_intervention/intervention_rollouts.csv
runs/m734_sequence_command_response_intervention/sequence_critical_rows.csv
runs/m734_sequence_command_response_intervention/sentinel_rows.csv
docs/m735-sequence-level-command-response-intervention-audit.md
```

The exporter should not need a checkpoint and should not instantiate an
optimizer. It is a deterministic CSV/JSON transform.

## Positive Row Selection

Positive sequence-outcome rows are:

```text
sequence_outcome_critical == true
sentinel == false
source_role != sentinel
normal_success == true or normal_margin >= 0
```

Registered expected count from M735:

```text
positive_rows: 70
```

The exporter must not count these as positives:

```text
sentinel rows
sequence_action_critical-only rows
temporal_action_critical-only rows
normal-failed rows
rows with missing matched normal rollout
```

Recommended positive identity key:

```text
source_index
seed
step
preferred_fault_family
wrong_fault_family
fault_family_pair
variant
horizon
```

Duplicate positives with the same identity key should be rejected and counted
in the summary.

## Contrast Rows

For each positive row, M737 should export a contrast group:

```text
contrast_group_id:
  source_index + horizon + positive variant

normal row:
  same source_index
  same horizon
  variant == normal

positive intervention row:
  the non-sentinel sequence_outcome_critical row

optional hard negative rows:
  same source_index
  same horizon
  sequence_action_critical == true
  sequence_outcome_critical == false
  sentinel == false
```

The hard negatives are not proof rows. They are useful later if a sequence loss
needs to separate action-only sensitivity from terminal outcome sensitivity.
They must be marked with:

```text
contrast_role == hard_negative_action_only
proof_positive == false
```

M737 should cap hard negatives to avoid drowning the outcome rows:

```text
max_hard_negatives_per_positive: 2
selection: highest prefix_l2_mean then highest margin_gap_from_normal
```

## Export Artifacts

M737 should write:

```text
runs/m737_sequence_outcome_corpus_export/summary.json
runs/m737_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
runs/m737_sequence_outcome_corpus_export/contrast_rows.csv
runs/m737_sequence_outcome_corpus_export/hard_negative_rows.csv
runs/m737_sequence_outcome_corpus_export/excluded_sentinel_rows.csv
runs/m737_sequence_outcome_corpus_export/rejected_rows.csv
runs/m737_sequence_outcome_corpus_export/source_balance.csv
runs/m737_sequence_outcome_corpus_export/variant_horizon_balance.csv
docs/m737-sequence-outcome-corpus-export-implementation.md
```

Required columns for every exported contrast row:

```text
contrast_group_id
contrast_role
proof_positive
source_index
source_role
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
source_pool
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
sentinel
```

The exporter should preserve numeric values as numeric JSON fields in the
summary and must write strict JSON without `NaN`.

## Corpus Gates

Positive corpus gate:

```text
positive_rows >= 50
positive_sentinel_rows == 0
positive_source_role_sentinel_rows == 0
duplicate_positive_keys == 0
missing_normal_matches == 0
unique_positive_seeds >= 20
unique_positive_fault_family_pairs >= 6
max_positive_seed_dominance <= 0.15
```

Contrast gate:

```text
contrast_groups == positive_rows
normal_rows == positive_rows
positive_intervention_rows == positive_rows
hard_negative_rows >= positive_rows
hard_negative_rows <= 2 * positive_rows
```

Variant and horizon gate:

```text
positive_horizons include at least 4 and 8
positive_variants include zero_command_obs
variant_horizon_balance.csv reports all observed combinations
```

Sentinel gate:

```text
excluded_sentinel_rows >= 3
sentinel_false_positive_rows_exported_as_positive == 0
```

The expected sentinel count is `3` from M735, but the gate should allow more if
M734 is rerun later.

## Result Classes

M737 should classify its result as one of:

```text
sequence_outcome_corpus_exported:
  all positive, contrast, diversity, and sentinel gates pass

sequence_outcome_corpus_sparse:
  sentinel filtering leaves fewer than 50 positives

sequence_outcome_corpus_unbalanced:
  positives exist but source or fault-family dominance exceeds gate

sequence_outcome_corpus_artifact:
  sentinel rows, action-only rows, duplicates, or missing normal matches enter
  the positive corpus
```

Only `sequence_outcome_corpus_exported` can admit an audit or objective-design
decision. It still cannot admit PPO or checkpoint promotion directly.

## M737 Command

Registered implementation command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.sequence_outcome_corpus_export \
  --summary runs/m734_sequence_command_response_intervention/summary.json \
  --rollouts runs/m734_sequence_command_response_intervention/intervention_rollouts.csv \
  --sequence-critical-rows runs/m734_sequence_command_response_intervention/sequence_critical_rows.csv \
  --sentinel-rows runs/m734_sequence_command_response_intervention/sentinel_rows.csv \
  --run-dir runs/m737_sequence_outcome_corpus_export \
  --max-hard-negatives-per-positive 2
```

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q \
  tests/test_sequence_outcome_corpus_export.py \
  tests/test_research_validate.py \
  tests/test_research_manifest.py \
  tests/test_research_cycle.py
```

## Relation To Extreme Fault Coverage

The M736 export does not solve scenario coverage. It only preserves the first
clean sequence-outcome evidence.

The user's coverage concern is valid: current evidence can still be limited by
the hidden-condition taxonomy. After the M737 export and its audit, a later
branch should explicitly refresh the extreme-fault scenario distribution with
fault classes such as:

```text
single-wheel tire puncture or tire stiffness collapse
single-wheel or split-side friction loss
front/rear axle friction asymmetry
local ice/oil/gravel patch
brake fade, brake loss, and brake-balance anomaly
single-wheel brake failure
drive authority loss and halfshaft or driveline failure proxies
steering lag, limit, stuck, and rate-limit faults
sensor delay, dropout, bias, and noise
actuator deadzone and asymmetric lag
mass, CG, load-transfer, and payload shifts
fault onset during warm-up, pre-emergency, emergency, and recovery phases
```

The current single-track simulator cannot faithfully express every
single-wheel or driveline failure. The future distribution should therefore
separate:

```text
current-model proxy faults:
  asymmetric authority, delay, friction, and sensor/actuator disturbances

requires four-wheel or higher-fidelity engine:
  true single-wheel blowout, true halfshaft break, true wheel-specific brake
  failure, wheel-speed/normal-load/tire-temperature effects
```

That branch should produce matched counterfactual cases, not just a crash zoo:

```text
same current geometry and ego-visible state
different hidden fault condition
normal history vs reset / zero / delayed / wrong history
action and terminal margin divergence reported separately
```

M736 keeps that future work visible while preventing it from contaminating the
current sequence-outcome corpus export.

## Claims Allowed

If M737 passes, the project may claim:

```text
M734's sequence-outcome positives have been preserved as a compact
sentinel-filtered corpus with matched normal and intervention rows.
```

It still may not claim:

```text
the driver improved;
PPO is admissible;
the corpus generalizes to private holdout;
the current simulator covers all extreme vehicle failures.
```

The next required decision after export is an audit: either design a
sequence-preference objective, repeat the sequence diagnostic on refreshed
extreme-fault coverage, or run both in a staged order.
