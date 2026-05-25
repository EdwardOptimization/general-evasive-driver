# M802 V4 Low-Margin Source-Diverse Corpus Refresh Audit

## Purpose

M802 audits M801 before any boundary-window retargeting, residual calibration,
PPO, or checkpoint promotion.

The question is:

```text
Is M801 a clean low-margin corpus refresh result, and what should the next
blocker be?
```

This milestone is audit-only:

```text
no corpus rerun
no residual calibration
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Cleanliness Check

M801 preserved the intended no-training invariants:

```text
source wave actor_parameters_changed: false
sequence intervention actor_parameters_changed: false
reference replay actor_backbone_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

The new selector is artifact-only. It reads reference replay rows and writes
candidate, accepted, band-summary, and JSON artifacts. It does not load or
mutate model parameters.

## Coverage Result

M801 materially expanded public v4 source coverage:

```text
matched_pair_count: 49152
reset_only_rows: 3552
source_candidate_rows: 2048
sequence_outcome_critical_rows: 4825
unique_sequence_outcome_seeds: 108
unique_sequence_outcome_fault_family_pairs: 18
max_sequence_outcome_seed_dominance: 0.086425
sentinel_false_positive_rows: 0
```

The exported corpus also passed its normal metadata and positive-corpus gates:

```text
positive_rows: 4825
unique_positive_seeds: 108
unique_positive_fault_family_pairs: 18
max_positive_seed_dominance: 0.086425
max_positive_fault_family_pair_dominance: 0.137617
missing_normal_matches: 0
positive_rows_missing_v4_metadata: 0
positive_rows_missing_fidelity_metadata: 0
positive_corpus_gate_pass: true
v4_metadata_gate_pass: true
```

So M801 is not a broad source-coverage failure. It disproves the simpler
explanation that M798 was blocked only because the source wave was too small.

## Reference Replay Result

The frozen M568 actor and frozen M761 residual head reconstruct almost all
fresh positives:

```text
positive_rows: 4825
reconstructed_rows: 4805
sample_reconstruction_success_rate: 0.995855
metadata_missing_rows: 0
rejected_rows: 20
```

But the raw residual reference replay regresses normal-history safety for every
nonzero alpha:

```text
alpha 0.125 normal success: 0.987513
alpha 0.125 normal collision: 0.012487

alpha 0.2 normal success: 0.987513
alpha 0.2 normal collision: 0.012487
```

The intervention gap increases, but the replay is not a candidate:

```text
alpha 0.2 intervention_action_gap_mean_vs_normal: 0.048074
candidate_alpha_count: 0
result_class: v4_residual_closed_loop_replay_normal_regression
```

This is acceptable for M801 because the reference replay is diagnostic only.
It reinforces that residual-assisted low-margin rows sit near a real
collision/success transition.

## Low-Margin Guard Result

The primary M800 gate was:

```text
normal branch
alpha == 0.2
normal_success == true
normal_collision == false
0.0 <= min_clearance_margin <= 0.00005
```

M801 result:

```text
accepted_low_margin_guard_row_count: 0
fresh_accepted_low_margin_guard_row_count: 0
low_margin_corpus_pass: false
result_class: v4_low_margin_guard_refresh_diagnostic_band_only
```

Diagnostic bands for successful collision-free rows:

```text
<= 0.00005: 0 rows
<= 0.00010: 0 rows
<= 0.00050: 0 rows
<= 0.00100: 0 rows
<= 0.01000: 24 rows, 1 seed, 4 source indices, 3 fault pairs
<= 0.10000: 39 rows, 5 seeds, 12 source indices, 4 fault pairs
<= 0.20000: 76 rows, 9 seeds, 41 source indices, 11 fault pairs
```

A direct check of all normal alpha `0.2` rows explains the gap:

```text
rows with margin <= 0.001: 60
  success: 0
  collision: 60
  seeds: 2
  fault-family pairs: 1

smallest collision-free successful margin: about 0.005243 m
```

The refreshed distribution produces collisions and safe-enough successes, but
not successful non-collision rows in the very low margin primary window.

## Classification

M801 should be classified as:

```text
v4_low_margin_guard_refresh_diagnostic_band_only
```

Failure taxonomy:

```text
scenario_sampling_failure
```

More specific label:

```text
boundary_window_miss
```

Rejected labels:

```text
not contract_violation
not training_instability
not private_holdout_contamination
not proof_washout
not promotion_gate_failure
```

The selector and replay artifacts are internally consistent, so this is not a
metric artifact in the narrow sense. The `metric_artifact` risk remains only if
we tried to convert diagnostic bands into primary evidence after seeing the
result.

## Supported Claims

M802 supports:

```text
1. M801 is a clean no-training data and selector result.

2. Public v4 sequence-outcome coverage increased materially over M773.

3. The active-steer guard blocker is now sharper: broad source coverage is
   available, but primary low-margin successful non-collision rows are absent.

4. The next step should target the collision/success boundary window directly,
   not run another generic broad source wave or relax the primary threshold.
```

## Falsified Claims

M802 falsifies:

```text
1. Doubling the source wave is sufficient to produce the requested
   source-diverse low-margin guard corpus.

2. M801 admits active-steer calibration.

3. Diagnostic rows at 0.005 m to 0.2 m should be treated as equivalent to the
   primary <= 0.00005 m gate.

4. PPO or checkpoint promotion should resume from this branch now.
```

## Next Design Requirements

M803 should be design-only. It should not run another broad source wave with
only larger seed count.

Instead, it should design a boundary-window retargeting step around the
collision/success transition found by M801:

```text
1. start from M801 collision rows and nearest non-collision diagnostic rows;
2. scan or bisect controllable public scenario axes such as obstacle timing,
   obstacle lateral offset, fault activation step, and fault severity;
3. optionally scan residual alpha only as a diagnostic to locate transition
   geometry, not to redefine the primary alpha 0.2 gate;
4. export candidate rows where alpha 0.2 normal branch is successful,
   collision-free, and margin <= 0.00005;
5. require source diversity before any calibration objective.
```

M803 should also add progress/sharding requirements for future long source
waves, because M801's source wave is long and writes only at completion.

## Decision

M802 admits:

```text
m803-v4-low-margin-boundary-window-retarget-design
```

Residual calibration, PPO, and checkpoint promotion remain blocked.
