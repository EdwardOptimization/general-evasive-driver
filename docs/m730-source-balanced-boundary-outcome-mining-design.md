# M730 Source-Balanced Boundary Outcome Mining Design

## Purpose

M730 designs a no-training boundary miner after M729 showed that M728 is
source-balanced but still action-only.

The question is:

```text
Can M728's source-balanced command-history action rows become outcome-critical
when evaluated near local obstacle and terminal-margin boundaries?
```

This is a design milestone only:

```text
no data wave
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Why M722 Is Not Enough

M722 already tested boundary mining, but its source pool was concentrated:

```text
M722 source rows: 128
M722 unique source seeds: 4
M722 temporal action-critical rows: 921
M722 temporal outcome-critical rows: 0
```

M728 changes the source condition:

```text
M728 selected pairs: 3951
M728 temporal action-critical rows: 2613
M728 unique temporal action seeds: 351
M728 temporal outcome-critical rows: 1
```

So the right next test is not another broad quota-only wave. It is a boundary
miner that starts from the broad M728 action-critical pool.

## Source Pool

Primary source rows:

```text
path: runs/m728_quota_calibrated_source_balanced_temporal_wave/temporal_critical_rows.csv
variant: mismatch_zero_command_history
temporal_action_critical: true
normal_success: true or normal_margin >= 0
first_action_distance_from_normal >= 0.015
```

Diagnostic singleton:

```text
seed: 72339
fault_family_pair: front_lateral_authority_drop->steering_fault
normal_margin: 0.001388798
variant_margin: -0.000232400
```

The singleton should be retained as a diagnostic seed but not counted as a
sufficient source-positive corpus.

Sentinel source rows:

```text
M728 rows with low first_action_distance_from_normal
M728 rows with healthy normal margins and no temporal sensitivity
M728 non-critical intervention_rollouts rows when available
```

## Required Loader Fix

M722's existing source loader deduplicates on `pair_id`, but M728 rows use
`proposal_id` and `selected_index`.

M731 must support both schemas:

```text
dedup id preference:
  pair_id
  proposal_id
  selected_index
  seed/step/variant/fault_family_pair fallback
```

Without this fix, rows from the same seed/step/variant can be collapsed
accidentally and source diversity can be undercounted.

## Source Balance

M731 should select a larger source set than M722:

```text
max_source_rows: 512
sentinel_fraction: 0.10
primary target: about 461
sentinel target: about 51
```

Balance over:

```text
seed
preferred_fault_family
wrong_fault_family
fault_family_pair
preferred_fault_severity
source_pool
step_bucket
normal_margin_bucket
first_action_distance_bucket
assigned_split
```

Minimum source-balance targets:

```text
unique_source_seeds >= 128
unique_preferred_fault_families >= 7
unique_fault_family_pairs >= 16
max_source_seed_dominance <= 0.02
max_source_family_dominance <= 0.25
sentinel_fraction between 0.05 and 0.15
```

If the source loader cannot satisfy these targets from M728 rows, M731 should
classify the result as source-balance blocked rather than silently lowering the
claim.

## Boundary Perturbations

M731 should rerun scenarios in memory and use structured environment relocation,
as M722 did. It must not mutate serialized strings or inject oracle labels into
actor observations.

Registered first wave:

```text
max_candidates_per_source: 16
obstacle_x_shifts: -16,-12,-8,-4,0,4,8
obstacle_y_shifts: -1.00,-0.75,-0.50,-0.25,0,0.25,0.50,0.75,1.00
half_width_deltas: 0,0.10,0.20,0.30
```

Candidate selection should not exhaust the full Cartesian grid. It should rank
candidates by:

```text
normal history remains viable;
variant first-action distance remains >= 0.015;
normal terminal margin is close to zero;
variant margin is lower than normal margin;
sentinel variants do not become false positives.
```

This keeps M731 a targeted boundary miner, not a brute-force scenario search.

## Intervention Variants

M731 should evaluate:

```text
normal
reset_hidden
mismatch_zero_command_history
delayed_hidden_20
pre_fault_stale_hidden
```

It should keep reports separate for:

```text
temporal action-critical rows
temporal outcome-critical rows
reset action-critical rows
reset outcome-critical rows
sentinel false positives
normal-history failures
history-insensitive failures
```

## Acceptance Gates

Outcome-positive gate:

```text
accepted_rows >= 20
temporal_outcome_critical_rows >= 20
unique_outcome_seeds >= 10
unique_outcome_fault_family_pairs >= 4
max_outcome_seed_dominance <= 0.20
sentinel_false_positive_rate <= 0.05
normal_history_retention_pass == true
actor_parameters_changed == false
```

Action-only gate:

```text
temporal_action_critical_rows >= 300
temporal_outcome_critical_rows < 20
sentinel_false_positive_rate <= 0.05
normal_history_retention_pass == true
```

Artifact/failure gates:

```text
normal_failed_rejected > 50% of candidate variants -> normal_failed_too_severe
sentinel_false_positive_rate > 0.05 -> boundary_miner_artifact
source-balance targets not met -> source_balance_blocked
candidate_variant_count == 0 -> boundary_miner_empty
```

## Claims Allowed

If M731 is outcome-positive, it can claim:

```text
source-balanced boundary mining found a corpus where command-history action
differences become closed-loop outcome differences.
```

It still cannot claim:

```text
trained driver improvement;
PPO readiness;
checkpoint promotion.
```

If M731 remains action-only, it supports:

```text
source-balanced action coupling is real, but one-step boundary perturbations
are still insufficient for closed-loop self-ID proof.
```

## M731 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.temporal_action_boundary_outcome_miner \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --temporal-rows runs/m728_quota_calibrated_source_balanced_temporal_wave/temporal_critical_rows.csv \
  --seed-start 72000 \
  --seed-count 512 \
  --max-source-rows 512 \
  --max-candidates-per-source 16 \
  --obstacle-x-shifts=-16,-12,-8,-4,0,4,8 \
  --obstacle-y-shifts=-1.00,-0.75,-0.50,-0.25,0,0.25,0.50,0.75,1.00 \
  --half-width-deltas=0,0.10,0.20,0.30 \
  --device cpu \
  --run-dir runs/m731_source_balanced_boundary_outcome_miner
```

M731 should include a small smoke first:

```text
seed_count: 16
max_source_rows: 32
max_candidates_per_source: 4
```

## Next Decision

If M731 is outcome-positive:

```text
audit and then export a compact source-balanced outcome corpus.
```

If M731 is source-balanced but action-only:

```text
audit and then choose between sequence-level command-response interventions and
explicit asymmetric/yaw-disturbance dynamics.
```

If M731 is source-balance blocked:

```text
repair source selection before any objective or PPO work.
```
