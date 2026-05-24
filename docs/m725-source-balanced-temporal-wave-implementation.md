# M725 Source-Balanced Temporal Wave Implementation

## Purpose

M725 implements and runs the no-training source-balanced temporal wave designed
in M724.

The question is:

```text
Can a pair-proposal-first, quota-selected temporal wave remove M719/M722
early-seed saturation and produce a more diverse temporal action/outcome corpus?
```

This milestone is diagnostic-only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Implementation

M725 adds:

```text
src/autodrift/source_balanced_temporal_wave.py
tests/test_source_balanced_temporal_wave.py
```

The runner:

```text
1. Reruns the v2 extreme-fault scenario family in memory.
2. Writes pair proposals before temporal intervention rollouts.
3. Selects proposals with deterministic source-balance quotas.
4. Evaluates temporal command-response variants only for selected proposals.
5. Writes source-balance, sentinel, variant, seed, family, and critical-row
   artifacts.
```

It preserves the actor-input contract. Hidden fault and scenario labels are used
only for generation, balancing, logging, and audit.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.source_balanced_temporal_wave \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --seed-start 72000 \
  --seed-count 512 \
  --selected-pair-count 4096 \
  --per-seed-pair-cap 8 \
  --device cpu \
  --run-dir runs/m725_source_balanced_temporal_wave
```

## Artifacts

```text
runs/m725_source_balanced_temporal_wave/summary.json
runs/m725_source_balanced_temporal_wave/scenario_summary.csv
runs/m725_source_balanced_temporal_wave/pair_proposals.csv
runs/m725_source_balanced_temporal_wave/selected_pair_proposals.csv
runs/m725_source_balanced_temporal_wave/source_rows.csv
runs/m725_source_balanced_temporal_wave/intervention_rollouts.csv
runs/m725_source_balanced_temporal_wave/temporal_critical_rows.csv
runs/m725_source_balanced_temporal_wave/sentinel_rows.csv
runs/m725_source_balanced_temporal_wave/rejected_rows.csv
runs/m725_source_balanced_temporal_wave/quota_summary.csv
runs/m725_source_balanced_temporal_wave/seed_summary.csv
runs/m725_source_balanced_temporal_wave/fault_family_summary.csv
runs/m725_source_balanced_temporal_wave/variant_summary.csv
```

## Result Summary

```text
result_class: source_balance_blocked

scenario_count:       16896
snapshot_count:       72056
proposal_count:       69591
selected_pair_count:   2048
row_count:            21620

temporal_action_critical_rows:  1392
temporal_outcome_critical_rows:    0

sentinel_rows:                7031
sentinel_false_positive_rows:    0
sentinel_false_positive_rate:  0.0

unique_selected_seeds:        256
unique_temporal_action_seeds: 186
unique_temporal_outcome_seeds:  0

unique_preferred_fault_families: 7
unique_fault_family_pairs:      24

max_seed_dominance:              0.00390625
max_preferred_family_dominance:  0.3125
max_temporal_action_seed_dominance: 0.00647

normal_history_retention_pass: true
actor_parameters_changed:      false
training_started:              false
optimizer_started:             false
ppo_used:                      false
promoted:                      false
```

The wave improves seed diversity substantially relative to M722:

```text
M722 selected source seeds: 4
M725 selected source seeds: 256

M722 temporal action seeds: 4
M725 temporal action seeds: 186
```

But it fails the full registered source-balance gate:

```text
selected_pair_count target: 4096
selected_pair_count actual: 2048

unique_preferred_fault_families target: >= 8
unique_preferred_fault_families actual: 7

max_preferred_family_dominance target: <= 0.25
max_preferred_family_dominance actual: 0.3125
```

## Proposal vs Selected Distribution

The proposal table is broad:

```text
proposal_count: 69591
proposal preferred families: 9
proposal fault-family pairs: 40
proposal step buckets: 2
```

Top proposal preferred families:

```text
combined_fault:                17465
global_mu_drop:                 8721
mass_cg_shift:                  6580
drive_authority_drop:           6567
brake_authority_drop:           6526
front_lateral_authority_drop:   6446
steering_fault:                 6440
rear_lateral_authority_drop:    6430
delay_noise_fault:              4416
```

The selected table is seed-balanced but over-constrained:

```text
selected_pair_count: 2048
unique_selected_seeds: 256
per selected seed: 8 rows

step_bucket 1: 1024
step_bucket 2: 1024
```

The registered `per_step_bucket_cap=1024` combined with only two step buckets
created a hard ceiling of 2048 selected rows. This is a quota design issue, not
a lack of available proposals.

## Variant Breakdown

```text
mismatch_zero_command_history:
  rows:                         2048
  temporal action-critical:     1390
  temporal outcome-critical:       0
  first action distance mean: 0.021091
  first action distance max:  0.033441
  margin gap max:            0.005286

reset_hidden:
  rows:                         2048
  action-critical:              1394
  outcome-critical:                0
  first action distance mean: 0.020014
  margin gap max:            0.004695

cross_fault_wrong_hidden:
  rows:                         2048
  action-critical:                 0
  outcome-critical:                0
  first action distance max:  0.012911
  margin gap max:            0.000271

delayed_hidden_20:
  rows:                         2048
  temporal action-critical:        1
  temporal outcome-critical:       0
  margin gap max:            0.001118

pre_fault_stale_hidden:
  rows:                         1140
  temporal action-critical:        1
  temporal outcome-critical:       0
  margin gap max:            0.000496
```

## Interpretation

M725 partially fixes the source coverage concern:

```text
source seed diversity improves from 4 to 256 seeds,
and temporal action rows improve from 4 to 186 action-positive seeds.
```

It does not yet produce a fully admissible source-balanced wave because the
quota design over-constrained step buckets:

```text
selected_pair_count stopped at 2048 even though 69591 proposals existed.
```

It also remains outcome-negative:

```text
temporal_outcome_critical_rows: 0
```

This is still valuable. It says:

```text
the command-history action signal survives source balancing,
but closed-loop outcome evidence still needs either a quota-calibrated full
wave plus boundary mining, sequence-level interventions, or higher-fidelity
fault dynamics.
```

## Supported Claims

M725 supports:

```text
1. The pair-proposal-first runner is executable and writes the registered
   artifacts.

2. M719/M722 source concentration was real and can be substantially reduced.

3. `mismatch_zero_command_history` remains the dominant temporal action signal
   after source balancing.

4. Sentinel false positives remain zero.

5. The current actor/input contract remains clean.
```

## Falsified Claims

M725 falsifies:

```text
1. The M719/M722 action signal was only an early-seed artifact.

2. Source balancing alone is sufficient to produce outcome-critical temporal
   rows.

3. The registered M724 quota settings are already calibrated for a full 4096
   selected-pair wave.

4. M725 justifies source export, actor update, PPO, or promotion.
```

M725 does not falsify:

```text
1. A quota-calibrated full wave may pass source-balance gates.

2. A source-balanced boundary miner may still convert action rows into outcome
   rows.

3. Sequence-level interventions may be required if single-step temporal action
   differences remain outcome-neutral.

4. True asymmetric faults may require four-wheel or explicit-yaw-disturbance
   dynamics.
```

## Failure Taxonomy

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
The selected wave fails the registered source-balance gates because quota caps
produce only 2048 selected pairs and preferred-family dominance remains above
threshold.
```

Secondary:

```text
metric_artifact
```

Reason:

```text
The run has 1392 temporal action-critical rows but 0 temporal outcome-critical
rows. Action rows remain diagnostic, not closed-loop proof.
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

M726 should audit the M725 result before another run.

The audit should decide whether to:

```text
1. run a quota-calibrated M727 wave with a larger per-step-bucket cap;
2. lower selected-pair target by registering a smaller scale with matching
   source-balance thresholds;
3. proceed to boundary mining only after source-balance gates pass;
4. pivot to sequence-level intervention design if action-only evidence remains
   outcome-neutral after quota calibration.
```
