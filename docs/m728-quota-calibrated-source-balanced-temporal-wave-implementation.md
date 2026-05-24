# M728 Quota-Calibrated Source-Balanced Temporal Wave Implementation

## Purpose

M728 runs the no-training quota-calibrated temporal wave designed in M727.

The question is:

```text
If the M725 step-bucket quota artifact is removed, does the v2 extreme-fault
wave produce source-balanced temporal action/outcome evidence?
```

This milestone is diagnostic-only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Commands

Smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_balanced_temporal_wave \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --seed-start 72000 \
  --seed-count 2 \
  --selected-pair-count 16 \
  --per-seed-pair-cap 8 \
  --per-fault-family-pair-cap 256 \
  --per-preferred-family-cap 640 \
  --per-step-bucket-cap 4096 \
  --device cpu \
  --run-dir runs/m728_quota_calibrated_source_balanced_temporal_wave_smoke
```

Registered run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_balanced_temporal_wave \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --seed-start 72000 \
  --seed-count 512 \
  --selected-pair-count 4096 \
  --per-seed-pair-cap 8 \
  --per-fault-family-pair-cap 256 \
  --per-preferred-family-cap 640 \
  --per-step-bucket-cap 4096 \
  --device cpu \
  --run-dir runs/m728_quota_calibrated_source_balanced_temporal_wave
```

## Artifacts

```text
runs/m728_quota_calibrated_source_balanced_temporal_wave/summary.json
runs/m728_quota_calibrated_source_balanced_temporal_wave/scenario_summary.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/pair_proposals.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/selected_pair_proposals.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/source_rows.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/intervention_rollouts.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/temporal_critical_rows.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/sentinel_rows.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/rejected_rows.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/quota_summary.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/seed_summary.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/fault_family_summary.csv
runs/m728_quota_calibrated_source_balanced_temporal_wave/variant_summary.csv
```

## Result Summary

```text
result_class: source_balanced_temporal_action_only

scenario_count:       16896
snapshot_count:       72056
proposal_count:       69591
selected_pair_count:   3951
row_count:            41238

temporal_action_critical_rows: 2613
temporal_outcome_critical_rows:   1

sentinel_rows:                13176
sentinel_false_positive_rate:   0.0

unique_selected_seeds:        494
unique_temporal_action_seeds: 351
unique_temporal_outcome_seeds:  1

unique_preferred_fault_families: 9
unique_fault_family_pairs:      33

max_seed_dominance:              0.002025
max_preferred_family_dominance:  0.161984
max_temporal_action_seed_dominance: 0.003827

normal_history_retention_pass: true
actor_parameters_changed:      false
training_started:              false
optimizer_started:             false
ppo_used:                      false
promoted:                      false
```

M728 removes the M725 source-balance blocker:

```text
M725 selected_pair_count: 2048
M728 selected_pair_count: 3951

M725 unique_selected_seeds: 256
M728 unique_selected_seeds: 494

M725 unique_preferred_fault_families: 7
M728 unique_preferred_fault_families: 9

M725 max_preferred_family_dominance: 0.3125
M728 max_preferred_family_dominance: 0.161984
```

M728 still misses the exact requested `4096` selected-pair target:

```text
selected_pair_target: 4096
selected_pair_actual: 3951
```

This is not the M725 hard step-bucket cap. The selected table is now broad and
passes the source-balance thresholds used by `classify_source_balanced_temporal_wave`.

## Selected Distribution

Preferred families:

```text
brake_authority_drop:          640
combined_fault:                640
drive_authority_drop:          640
global_mu_drop:                640
front_lateral_authority_drop:  640
mass_cg_shift:                 342
delay_noise_fault:             256
rear_lateral_authority_drop:   149
steering_fault:                  4
```

Step buckets:

```text
step_bucket 1: 2212
step_bucket 2: 1739
```

Top family pairs:

```text
brake_authority_drop->brake_authority_drop:          256
brake_authority_drop->combined_fault:                256
combined_fault->brake_authority_drop:                256
delay_noise_fault->steering_fault:                   256
drive_authority_drop->combined_fault:                256
drive_authority_drop->drive_authority_drop:          256
global_mu_drop->combined_fault:                      256
mass_cg_shift->combined_fault:                       256
front_lateral_authority_drop->combined_fault:        256
front_lateral_authority_drop->steering_fault:        256
```

## Variant Breakdown

Dominant temporal action signal:

```text
mismatch_zero_command_history:
  rows:                         3951
  temporal action-critical:     2609
  temporal outcome-critical:       1
  first action distance mean: 0.021337
  first action distance max:  0.035347
  margin gap max:            0.006935
```

Reset hidden:

```text
reset_hidden:
  rows:                         3951
  action-critical:              2619
  outcome-critical:                0
  first action distance mean: 0.020168
  margin gap max:            0.005925
```

Cross-fault wrong hidden:

```text
cross_fault_wrong_hidden:
  rows:                         3951
  action-critical:                 0
  outcome-critical:                0
  first action distance max:  0.014178
  margin gap max:            0.000532
```

Delayed and response-delay variants remain mostly action-neutral:

```text
delayed_hidden_20 temporal action-critical rows: 2
pre_fault_stale_hidden temporal action-critical rows: 2
all other delayed/shift response variants: 0 temporal action-critical rows
```

## Outcome Singleton

M728 finds exactly one temporal outcome-critical row:

```text
seed: 72339
variant: mismatch_zero_command_history
fault_family_pair: front_lateral_authority_drop->steering_fault
preferred_fault: front_puncture_proxy_moderate
wrong_fault: steering_lag_authority_moderate
step: 32
obstacle_distance: 13.223476
obstacle_lateral_offset: -2.152513
normal_success: true
variant_success: false
normal_margin: 0.001388798
variant_margin: -0.000232400
margin_gap_from_normal: 0.001621198
first_action_distance_from_normal: 0.023885543
terminal_reason: collision
```

This row is useful as a diagnostic seed, but one row is far below the registered
outcome gate:

```text
temporal_outcome_critical_rows target: >= 20
actual: 1
```

## Interpretation

M728 answers the immediate M726 question:

```text
M725 was indeed under-mined because of quota settings.
```

After quota calibration, source coverage is much stronger and the action signal
is clearly source-diverse:

```text
2613 temporal action-critical rows across 351 seeds.
```

But it also gives a sharper negative result:

```text
source-balanced temporal command-response action coupling still rarely changes
closed-loop outcome under the current one-step temporal variants and v2
extreme-fault scenario family.
```

This means the next question is no longer simply "did we mine enough source
families?" The next question is:

```text
Why does a robust action-level command-history signal fail to become
outcome-critical except for one near-boundary row?
```

Likely explanations:

```text
1. The selected rows are not close enough to terminal clearance boundaries.

2. The temporal intervention is too local: one-step action differences may be
   corrected by later closed-loop feedback.

3. The current single-track proxy faults are not asymmetric/yaw-rich enough to
   create many outcome-sensitive failure surfaces.

4. Outcome thresholds may be too coarse for early weak signal, but lowering
   them would not justify closed-loop self-ID proof.
```

## Supported Claims

M728 supports:

```text
1. Source-balanced temporal command-history action coupling exists.

2. M725's selected-pair shortage was a quota artifact.

3. The dominant useful intervention remains zeroing/mismatching previous
   command history, not cross-fault hidden replacement.

4. The current actor is sensitive to its physical command history over hundreds
   of seeds.

5. Actor parameters and actor inputs remain unchanged.
```

## Falsified Claims

M728 falsifies:

```text
1. Quota calibration alone is enough to produce an outcome-positive corpus.

2. The current v2 source-balanced temporal wave justifies source export,
   actor update, PPO, or promotion.

3. Cross-fault wrong hidden is currently the strongest intervention.
```

M728 does not falsify:

```text
1. Boundary mining around source-balanced action rows may produce outcome rows.

2. Sequence-level command-response interventions may produce stronger outcome
   effects than first-action mismatch.

3. More physical asymmetric/yaw-disturbance or four-wheel faults may be needed.
```

## Failure Taxonomy

Primary:

```text
metric_artifact
```

Reason:

```text
The run has strong source-balanced action evidence but only one outcome row.
Action-level criticality remains a diagnostic metric, not proof of closed-loop
self-identification.
```

Secondary:

```text
scenario_sampling_failure
```

Reason:

```text
The calibrated wave did not produce enough outcome-boundary rows under the
current v2 scenario family and one-step temporal interventions.
```

Not classified as:

```text
training_instability:
  no training occurred.

contract_violation:
  actor observations were unchanged.

proof_washout:
  actor parameters were unchanged.
```

## Next Step

M729 should audit the M728 action-only result before launching another miner.

The audit should decide between:

```text
1. source-balanced boundary mining around the 2613 action-critical rows;
2. sequence-level command-response interventions that execute a short action
   sequence before replanning;
3. explicit asymmetric/yaw-disturbance or four-wheel dynamics-fidelity work;
4. preserving the single outcome row as a diagnostic seed but not as a corpus.
```
