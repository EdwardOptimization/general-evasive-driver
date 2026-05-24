# M733 Sequence-Level Command-Response Intervention Design

## Purpose

M733 designs the next no-training experiment after M732 audited M731 as a clean
source-balanced action-only boundary result.

The question is:

```text
Does command-response history become outcome-critical if the intervention
persists over a short sequence instead of only changing the initial hidden
state or first action?
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

## Why Sequence-Level Intervention

M728 and M731 both show strong action dependence:

```text
M728 temporal action-critical rows: 2613
M731 temporal action-critical rows: 5881
```

But outcome rows stay sparse:

```text
M728 temporal outcome rows: 1
M731 accepted outcome rows: 1
```

The current interpretation is:

```text
one-step command-history action differences are often corrected by later
closed-loop feedback before terminal outcome changes.
```

The next direct test is to persist the history intervention for several control
steps while keeping the physical environment and actor parameters unchanged.

## Source Rows

M734 should start from M731 source rows and optionally include M728 action rows
as fallback.

Primary:

```text
path: runs/m731_source_balanced_boundary_outcome_miner/source_rows.csv
source_role: primary
variant: mismatch_zero_command_history
first_action_distance_from_normal >= 0.015
```

Secondary:

```text
path: runs/m728_quota_calibrated_source_balanced_temporal_wave/temporal_critical_rows.csv
variant: mismatch_zero_command_history
temporal_action_critical: true
normal_success: true or normal_margin >= 0
```

Sentinels:

```text
M731 source_role == sentinel
M728 low-action-distance rows with healthy normal margins
```

Initial registered scale:

```text
max_source_rows: 512
sentinel_fraction: 0.10
```

Source balance should cover:

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

## Intervention Semantics

M734 should rerun the seed/fault scenarios in memory and replay from the
decision snapshot.

Normal rollout:

```text
At every step:
  actor sees the true human-view observation from the environment
  recurrent hidden is updated normally
  action is applied to the environment
```

Sequence intervention rollout:

```text
For the first H steps:
  actor observation is copied and intervention-corrupted before policy
  recurrent hidden is updated from the corrupted observation
  action from the corrupted observation is applied to the real environment

After H steps:
  actor receives true observations again
  hidden continues from the intervention-updated hidden
```

This is a diagnostic counterfactual, not a deployable input change. The actor
contract is preserved because no hidden parameter or oracle field is added.

## Variants

M734 should evaluate:

```text
normal
zero_command_obs_H
command_shift_obs_H
response_delay_obs_H
reset_hidden_then_normal_H
reset_hidden_each_step_H
```

Required horizons:

```text
H in {2, 4, 6, 8}
```

Variant definitions:

```text
zero_command_obs_H:
  zero previous physical command fields in the actor observation for H steps.

command_shift_obs_H:
  replace previous command fields with the previous replay observation's
  command fields for H steps.

response_delay_obs_H:
  replace ego-response dimensions with a delayed observation when available.

reset_hidden_then_normal_H:
  reset hidden at the decision step only, then run normally.

reset_hidden_each_step_H:
  reset hidden before each of the first H policy evaluations.
```

Optional after smoke:

```text
hold_wrong_hidden_H:
  use cross-fault wrong hidden for the first H steps if a matched wrong snapshot
  can be reconstructed cleanly.
```

## Metrics

Each rollout row should report:

```text
source metadata
variant
horizon
normal_success
variant_success
normal_margin
variant_margin
margin_gap_from_normal
success_drop_from_normal
first_action_distance_from_normal
trajectory_l2_mean
trajectory_l2_max
prefix_l2_mean
prefix_l2_max
terminal_reason
temporal_action_critical
temporal_outcome_critical
sequence_action_critical
sequence_outcome_critical
sentinel flag
```

Action-critical:

```text
normal viable
variant != normal
trajectory_l2_mean over first H steps >= 0.015
```

Outcome-critical:

```text
normal viable
variant != normal
success drop
or margin_gap_from_normal >= 0.02
```

## Gates

Source-balance gate:

```text
source_candidate_rows >= 256
unique_source_seeds >= 128
unique_source_preferred_fault_families >= 7
unique_source_fault_family_pairs >= 16
source_max_seed_dominance <= 0.02
source_max_family_dominance <= 0.25
sentinel_fraction between 0.05 and 0.15
```

Sequence action gate:

```text
sequence_action_critical_rows >= 300
unique_sequence_action_seeds >= 50
```

Sequence outcome gate:

```text
sequence_outcome_critical_rows >= 20
unique_sequence_outcome_seeds >= 10
unique_sequence_outcome_fault_family_pairs >= 4
max_sequence_outcome_seed_dominance <= 0.20
sentinel_false_positive_rate <= 0.05
normal_history_retention_pass == true
actor_parameters_changed == false
```

Failure classes:

```text
sequence_outcome_positive:
  source balance and outcome gate pass.

sequence_action_only:
  source balance and action gate pass, but outcome gate fails.

sequence_source_balance_blocked:
  source balance gate fails.

sequence_artifact:
  sentinel false positives or actor checksum fail.

sequence_neutral:
  no meaningful sequence action rows.
```

## M734 Command

Smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.sequence_command_response_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --source-rows runs/m731_source_balanced_boundary_outcome_miner/source_rows.csv \
  --seed-start 72000 \
  --seed-count 16 \
  --max-source-rows 32 \
  --horizons 2,4 \
  --device cpu \
  --run-dir runs/m734_sequence_command_response_intervention_smoke
```

Registered run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.sequence_command_response_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --source-rows runs/m731_source_balanced_boundary_outcome_miner/source_rows.csv \
  --seed-start 72000 \
  --seed-count 512 \
  --max-source-rows 512 \
  --horizons 2,4,6,8 \
  --device cpu \
  --run-dir runs/m734_sequence_command_response_intervention
```

## Expected Artifacts

```text
runs/m734_sequence_command_response_intervention/summary.json
runs/m734_sequence_command_response_intervention/source_rows.csv
runs/m734_sequence_command_response_intervention/intervention_rollouts.csv
runs/m734_sequence_command_response_intervention/sequence_critical_rows.csv
runs/m734_sequence_command_response_intervention/sentinel_rows.csv
runs/m734_sequence_command_response_intervention/rejected_rows.csv
runs/m734_sequence_command_response_intervention/variant_summary.csv
runs/m734_sequence_command_response_intervention/horizon_summary.csv
runs/m734_sequence_command_response_intervention/fault_family_summary.csv
```

## Next Decision

If M734 is outcome-positive:

```text
audit and then export a compact sequence-outcome corpus.
```

If M734 is source-balanced action-only:

```text
audit and promote to asymmetric/yaw-disturbance dynamics fidelity design.
```

If M734 is source-balance blocked:

```text
repair source selection before interpreting the negative.
```
