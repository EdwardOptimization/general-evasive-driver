# M724 Fresh Source-Balanced Temporal Wave Design

## Purpose

M724 designs a fresh no-training temporal command-response data wave after M723
identified M719/M722 source concentration as the immediate blocker.

The working hypothesis is:

```text
M719 found real temporal action coupling, but its pair selection filled
max_pairs from early seeds. A fresh wave with source-balanced pair selection may
produce a more diverse temporal action corpus and a better basis for outcome
boundary mining.
```

This milestone is design-only:

```text
no implementation
no data wave
no source export
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

It admits only a no-training M725 implementation.

## Background

M719 produced:

```text
temporal_action_critical_rows:  3114
temporal_outcome_critical_rows:    0
unique_temporal_fault_families:    9
unique_temporal_seeds:            22
```

M722 then tried to mine outcomes around those rows:

```text
source_candidate_rows:          128
candidate_variant_count:       6984
temporal_action_critical_rows:  921
temporal_outcome_critical_rows:   0
sentinel_false_positive_rate:   0.0
```

M723 audited the key problem:

```text
M722 selected source rows from only 4 seeds.
```

The reason is structural. M719 iterated sorted seeds and stopped once
`max_pairs` was reached:

```text
for seed in sorted(snapshots_by_seed):
  for snapshot in fault_snapshots:
    ...
    pair_id += 1
    if pair_id >= max_pairs:
      break
```

That is useful for a quick diagnostic, but it is not enough for the next claim.
M725 should prevent early-seed saturation by construction.

## Design Principle

M725 should separate:

```text
pair proposal generation
source-balanced proposal selection
temporal intervention rollout
critical-row classification
sentinel allocation
```

The current M719 runner conflates proposal order and accepted row order. M725
should first build a proposal table across all seeds, then select from that
table using quotas.

## Pair Proposal Phase

M725 should rerun the v2 scenario family in memory, as M719 did, but write pair
proposals before running every temporal intervention:

```text
runs/m725_source_balanced_temporal_wave/pair_proposals.csv
```

Each proposal row should include:

```text
proposal_id
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
pairing_rule
match_distance
feature_distance
obstacle_distance
obstacle_lateral_offset
source_pool
assigned_split
step_bucket
obstacle_distance_bucket
```

Proposal generation may still use cross-fault matching, but it must not stop
after early seeds fill the global cap.

## Source-Balanced Selection

M725 should select proposals by quota before temporal rollout.

Recommended registered scale:

```text
seed_count:                 512
max_pair_proposals:       12000 or more if available
selected_pair_count:       4096
per_seed_pair_cap:            8
per_fault_family_pair_cap:  256
per_preferred_family_cap:   640
per_step_bucket_cap:       1024
```

If compute is too high, M725 may register a staged wave:

```text
Stage A smoke:
  seed_count: 16
  selected_pair_count: 128

Stage B registered wave:
  seed_count: 512
  selected_pair_count: 4096
```

But source-balance thresholds must be attached to the scale actually run.

Selection should use deterministic round-robin strata:

```text
seed
preferred_fault_family
wrong_fault_family
preferred_fault_severity
wrong_fault_severity
step_bucket
source_pool
assigned_split
```

Tie-breakers:

```text
lower match_distance
higher feature_distance
earlier and later step buckets alternated
heldout split retained, not optimized
stable sort by proposal_id
```

Target selected proposal diversity for the full wave:

```text
selected_pair_count >= 3000
unique_selected_seeds >= 128
unique_preferred_fault_families >= 8
unique_fault_family_pairs >= 24
max_seed_dominance <= 0.02
max_preferred_family_dominance <= 0.25
heldout_fraction between 0.15 and 0.25
```

If the selected proposal table cannot meet these thresholds, M725 should return:

```text
result_class: source_balance_blocked
```

and should not proceed to source export or actor objective design.

## Temporal Intervention Rollout

For each selected proposal, M725 should evaluate the same temporal variants as
M719:

```text
normal
reset_hidden
cross_fault_wrong_hidden
delayed_hidden_5
delayed_hidden_10
delayed_hidden_20
pre_fault_stale_hidden
mismatch_zero_command_history
mismatch_command_shift_1
mismatch_response_delay_5
mismatch_response_delay_10
```

The important variants remain:

```text
mismatch_zero_command_history
reset_hidden
delayed_hidden_20
pre_fault_stale_hidden
```

The current actor observation at the decision step must remain unchanged. Only
the recurrent hidden state is intervened on.

## Sentinel Allocation

Sentinels must be sampled from the same selected wave, not added only after a
positive result.

M725 should explicitly write:

```text
runs/m725_source_balanced_temporal_wave/sentinel_rows.csv
```

Sentinel candidates:

```text
normal viable
variant != normal
first_action_distance_from_normal < 0.005
normal_margin > 0.5
source-balanced by seed and fault family
```

Target:

```text
sentinel_rows >= 10% of selected temporal source rows
unique_sentinel_seeds >= 40 for full wave
sentinel_false_positive_rate <= 0.05
```

Sentinels are not source-positive proof. They are a false-positive guard.

## Row-Level Gates

Action-critical:

```text
normal_success == true or normal_margin >= 0
variant != normal
first_action_distance_from_normal >= 0.015
```

Outcome-critical:

```text
normal_success == true or normal_margin >= 0
variant != normal
and one of:
  success_drop_from_normal == true
  margin_gap_from_normal >= 0.02
```

Source-positive temporal row:

```text
temporal_variant == true
action-critical == true
```

Source-positive outcome row:

```text
temporal_variant == true
action-critical == true
outcome-critical == true
```

M725 may produce action-positive evidence without outcome-positive evidence.
Those must remain separate.

## Run-Level Classification

M725 should classify the result as one of:

```text
source_balanced_temporal_outcome_positive:
  source-balanced temporal action rows include source-diverse outcome-critical
  rows.

source_balanced_temporal_action_only:
  source-balanced temporal action rows are source-diverse, but outcome rows are
  below threshold.

source_balanced_temporal_sparse:
  source-balanced selection succeeds, but temporal action rows are too sparse.

source_balance_blocked:
  proposal or selected-pair diversity targets fail.

temporal_wave_artifact:
  sentinel false positives are high, actor checksum changes, hidden
  reconstruction is malformed, or actor input contract is violated.
```

## Run-Level Acceptance Thresholds

Full-wave source-balance acceptance:

```text
selected_pair_count >= 3000
unique_selected_seeds >= 128
unique_preferred_fault_families >= 8
unique_fault_family_pairs >= 24
max_seed_dominance <= 0.02
max_preferred_family_dominance <= 0.25
sentinel_false_positive_rate <= 0.05
normal_history_retention_pass == true
actor_parameters_changed == false
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
```

Full-wave action-positive acceptance:

```text
temporal_action_critical_rows >= 300
unique_temporal_action_seeds >= 40
unique_temporal_action_fault_families >= 6
max_temporal_action_seed_dominance <= 0.10
```

Full-wave outcome-positive acceptance:

```text
temporal_outcome_critical_rows >= 20
unique_temporal_outcome_seeds >= 10
unique_temporal_outcome_fault_families >= 4
max_temporal_outcome_family_dominance <= 0.40
```

These thresholds are deliberately separated so the project does not again turn
action-only evidence into closed-loop proof.

## Required Artifacts For M725

M725 should write:

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
docs/m725-source-balanced-temporal-wave-implementation.md
```

The summary must include:

```text
proposal_count
selected_pair_count
scenario_count
snapshot_count
row_count
temporal_action_critical_rows
temporal_outcome_critical_rows
sentinel_rows
sentinel_false_positive_rows
unique_selected_seeds
unique_temporal_action_seeds
unique_temporal_outcome_seeds
unique_preferred_fault_families
unique_fault_family_pairs
max_seed_dominance
max_preferred_family_dominance
max_temporal_action_seed_dominance
normal_history_retention_pass
actor_parameters_changed
training_started
optimizer_started
ppo_used
promoted
result_class
```

## M725 Command

M725 should implement and run:

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

A small smoke is allowed for implementation debugging, but M725's result class
must come from the registered wave or from a separately registered scale change.

## Supported Claims

M724 supports:

```text
1. The next blocker is source selection, not immediate PPO.

2. The next temporal wave must be balanced before intervention rollout claims
   are interpreted.

3. Sentinel rows should be first-class wave outputs.

4. Action and outcome evidence must remain separate.
```

## Falsified Claims

M724 falsifies:

```text
1. Raising max_pairs alone is a sufficient fix for M719/M722.

2. M722 action-only rows are enough to train or promote a driver.

3. Fresh boundary mining should proceed before fixing source concentration.
```

## Next Step

M725 should implement the no-training source-balanced temporal wave and classify
the result before any boundary miner rerun, actor objective design, PPO, or
model-fidelity branch.
