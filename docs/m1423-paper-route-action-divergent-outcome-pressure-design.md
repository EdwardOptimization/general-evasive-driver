# M1423 Paper-Route Action-Divergent Outcome-Pressure Design

## Summary

M1423 designs the next no-training evidence axis after M1421 showed that the
cleaner staged warmup source had zero warmup-history-positive outcome rows.

Decision:

```text
action_divergent_outcome_pressure_design_admit_source_constructor_implementation
```

M1423 does not run source smoke, outcome interventions, train, run PPO, promote,
use private holdout, export a training corpus, or change actor inputs.

## Failure Being Addressed

M1421 did not fail because the outcome probe could not run. It failed because
the source rows were not terminal-outcome sensitive to warmup-history variants:

```text
selected_candidate_rows: 252
outcome_rows: 2016
action_critical_rows: 1524
warmup_history_positive_rows: 0
accepted_zero_current_rows: 1
```

This says:

```text
history interventions often change actions;
those action changes almost never cross the terminal margin boundary.
```

So the next evidence axis should not be another staged warmup geometry retune.
It should explicitly target rows where:

```text
current observation is matched or near-matched;
history variants produce different action sequences;
terminal obstacle/road margin is close enough that the action difference matters.
```

## Design Principle

M1423 separates three concepts that were previously mixed:

```text
action-critical:
  intervention changes the action sequence.

outcome-critical:
  intervention changes success or clearance margin enough to matter.

history-necessary:
  warmup/wrong-history variants, not only reset or zero-current controls,
  produce outcome-critical degradation under matched-current conditions.
```

The next tool should not count action-critical rows as success. It should use
action divergence only as a candidate generator, then apply terminal-margin
pressure to test outcome sensitivity.

## Proposed Source Constructor

M1424 should implement a no-training constructor:

```text
autodrift.action_divergent_outcome_pressure
```

Inputs:

```text
checkpoint:
  runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt

config:
  configs/m1419_warmup_gate_invasiveness_retune_source_wave.json

source_candidates:
  runs/m1421_m1419_source_collision_stratified_outcome_probe/outcome_rows.csv
  runs/m1421_m1419_source_collision_stratified_outcome_probe/normal_margin_candidate_rows.csv
```

Candidate selection:

```text
1. keep rows with valid normal rollout and matched/bucketed source metadata;
2. keep rows with sequence_action_l2 >= 0.025 for a history variant;
3. prefer rows where current observation distance is low;
4. separate warmup-history variants from reset/zero-current controls;
5. reject rows where only zero-current creates action movement.
```

Terminal-margin pressure:

```text
For each candidate, try small obstacle/body-frame relocations or half-width
inflations that preserve the current observation/source structure but move the
normal rollout into a target margin band.
```

Allowed relocation variables:

```text
body_longitudinal_offset: [-2.0, -1.0, 0.0, 1.0, 2.0]
body_lateral_offset: [-0.4, -0.2, 0.0, 0.2, 0.4]
half_width_inflation: [0.0, 0.1, 0.2, 0.3]
```

Target margin bands:

```text
preferred_normal_margin: [0.02, 0.25]
broad_normal_margin: [0.00, 0.50]
```

Outcome pressure tests:

```text
normal_history_margin >= 0.0
history_variant_margin <= normal_history_margin - 0.02
or normal_history_success == true and history_variant_success == false
```

## Variants

History variants must be first-class:

```text
wrong_warmup_history_same_reveal
same_recent_wrong_warmup_history
delayed_warmup_history_8
delayed_warmup_history_16
warmup_removed
warmup_shortened_8
```

Controls must be reported but not counted as history-positive:

```text
reset_hidden
zero_current_response
```

If only reset or zero-current rows are found, the result is not positive
self-identification evidence.

## Gates

M1424 implementation should include a small smoke fixture and schema checks.
The first no-training source smoke after implementation should use these gates:

```text
candidate_rows >= 128
outcome_pressure_rows >= 32
history_positive_rows >= 16
history_positive_unique_source_seeds >= 6
history_positive_unique_capability_pairs >= 6
history_positive_unique_reveal_buckets >= 4
wrong_or_same_recent_positive_rows >= 4
max_single_seed_share <= 0.35
max_single_capability_pair_share <= 0.35
normal_history_success_rate >= 0.80
actor_parameters_changed == false
training_started == false
training_corpus_exported == false
```

These are public diagnostic gates, not promotion or paper-level gates.

## Required Outputs

The constructor should write:

```text
summary.json
candidate_rows.csv
outcome_pressure_rows.csv
history_positive_rows.csv
variant_summary.csv
source_diversity_summary.csv
relocation_summary.csv
rejected_rows.csv
```

The summary must report:

```text
action-critical count;
outcome-critical count;
history-positive count;
wrong-history-positive count;
reset/zero-current accepted count;
normal-margin bands;
collision/clear strata;
source seed/pair/bucket diversity;
contract flags.
```

## Forbidden Shortcuts

The next implementation must not:

```text
train
run PPO
export a training corpus
promote a checkpoint
use private holdout
change actor inputs
count zero-current as history-positive
count action divergence as outcome evidence
reuse staged warmup geometry retuning as the main evidence axis
```

## Next

Next milestone:

```text
m1424-paper-route-action-divergent-outcome-pressure-source-implementation
```

M1424 should implement the no-training constructor and focused tests only. It
should not run the full source smoke until the implementation passes tests and
the run manifest is separately registered.
