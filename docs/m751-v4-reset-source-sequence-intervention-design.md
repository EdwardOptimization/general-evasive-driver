# M751 V4 Reset-Source Sequence Intervention Design

## Purpose

M751 designs the next no-training experiment after M750 audited M749 as a broad
`cross_fault_reset_only` result.

The question is:

```text
Can M749's broader v4 reset-history-sensitive source surface become
outcome-sensitive when command-response interventions persist over a short
sequence?
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

## Why This Branch

M749 broadened extreme-fault coverage:

```text
scenario_count: 14848
matched_pair_count: 12288
reset_only_rows: 1171
wrong_history_action_critical_rows: 0
```

M750 audited this as:

```text
coverage is broad enough to produce recurrent-state sensitivity,
but the current cross-fault wrong-history swap is still not the right control
variable for deployed action or outcome evidence.
```

The M740 -> M743 chain already showed the useful pattern:

```text
reset-only evidence can become outcome-sensitive when the command-response
intervention persists for H steps.
```

So M751 should not run PPO. It should design a source-balanced M752 sequence
intervention over M749 reset-only rows.

## Source Rows

Primary source:

```text
runs/m749_extreme_fault_distribution_v4/reset_only_rows.csv
```

Available reset source surface:

```text
rows: 1171
unique seeds: 27
unique preferred fault families: 9
unique wrong fault families: 6
unique fault-family pairs: 17
max seed share: 0.139197
max preferred family share: 0.310845
max wrong family share: 0.349274
```

Primary eligibility:

```text
reset_history_action_critical == true
normal_margin >= 0
reset_action_l2_gap >= 0.015
source_role = primary
```

Sentinel source:

```text
runs/m749_extreme_fault_distribution_v4/rejected_rows.csv
```

Sentinel eligibility:

```text
rejection_reason == history_insensitive_too_mild
normal_margin > 0.5
action_l2_gap < 0.005
reset_margin_gap < 0.01
reset_action_l2_gap < 0.019
source_role = sentinel
```

The current M749 rejected rows provide enough sentinel candidates:

```text
sentinel candidates: 361
unique sentinel seeds: 23
```

## Source Adapter

M752 should use a v4-specific source adapter rather than directly reusing the
M743 `v3` labels.

The adapter should create source rows with at least:

```text
source_index
source_role
pair_id
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
source_pool
assigned_split
step_bucket
obstacle_distance_bucket
reset_action_l2_gap
reset_margin_gap
history_margin_gap
action_l2_gap
normal_margin
match_distance
feature_distance
pairing_rule
acceptance_reason
rejection_reason
source_kind
claim_boundary_level
```

For M749 rows, `fault_family_pair` should be reconstructed from
`preferred_fault_family` and `wrong_fault_family` if absent.

Expected source labels:

```text
source_pool:
  m749_v4_reset_only
  m749_v4_history_insensitive

source_kind:
  v4_reset_source
```

Fault metadata remains logging/source-selection metadata only. It must not be
added to actor observations.

## Source Balance

Initial M752 source targets:

```text
max_source_rows: 512
sentinel_fraction: 0.10
primary target: about 461
sentinel target: about 51
```

A precheck using the M743 source-selection logic on M749 rows gives:

```text
source_candidate_rows: 512
source_reset_rows: 461
source_sentinel_rows: 51
source_unique_seeds: 31
source_unique_preferred_fault_families: 9
source_unique_wrong_fault_families: 7
source_unique_fault_family_pairs: 21
source_max_seed_dominance: 0.121094
source_max_preferred_family_dominance: 0.126953
source_sentinel_fraction: 0.099609
```

Registered source gates:

```text
source_candidate_rows >= 512 if enough rows exist
source_unique_seeds >= 18
source_unique_preferred_fault_families >= 8
source_unique_wrong_fault_families >= 5
source_unique_fault_family_pairs >= 14
source_max_seed_dominance <= 0.16
source_max_preferred_family_dominance <= 0.25
sentinel_fraction between 0.05 and 0.15
```

## Intervention Semantics

M752 should reuse the M734/M743 sequence intervention semantics:

```text
For the first H steps:
  copy the actor observation
  corrupt command-response or hidden-history fields in the actor copy
  update recurrent hidden from the corrupted observation
  apply the resulting action to the real environment

After H steps:
  actor receives true observations again
  hidden continues from the intervention-updated hidden
```

No hidden parameter, fault label, feasibility label, TTC, or planner answer is
added to actor input.

## Variants

Registered variants:

```text
normal
zero_command_obs_H
response_delay_obs_H
reset_hidden_then_normal_H
reset_hidden_each_step_H
command_shift_obs_H
```

The first M752 wave should prioritize the M743-positive variants:

```text
zero_command_obs_H
reset_hidden_each_step_H
```

Registered horizons:

```text
H in {2, 4, 6, 8}
```

## Metrics

Each rollout row should report:

```text
source metadata
variant
horizon
normal_success
normal_margin
variant_success
variant_margin
margin_gap_from_normal
success_drop_from_normal
first action
trajectory_l2_mean
prefix_l2_mean
terminal_reason
sequence_action_critical
sequence_outcome_critical
sentinel
source_kind
claim_boundary_level
```

Action-critical:

```text
normal viable
variant != normal
max(prefix_l2_mean, trajectory_l2_mean) >= 0.015
```

Outcome-critical:

```text
normal viable
variant != normal
success drop
or margin_gap_from_normal >= 0.02
```

## Gates

Sequence action gate:

```text
sequence_action_critical_rows >= 400
unique_sequence_action_seeds >= 12
```

Sequence outcome gate:

```text
sequence_outcome_critical_rows >= 40
unique_sequence_outcome_seeds >= 10
unique_sequence_outcome_fault_family_pairs >= 6
max_sequence_outcome_seed_dominance <= 0.25
sentinel_false_positive_rate <= 0.05
normal_history_retention_pass == true
actor_parameters_changed == false
```

Failure classes:

```text
v4_reset_sequence_outcome_positive
v4_reset_sequence_action_only
v4_reset_source_balance_blocked
v4_reset_sequence_artifact
v4_reset_sequence_neutral
```

## M752 Command

Registered implementation command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v4_reset_source_sequence_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_scenarios.json \
  --reset-rows runs/m749_extreme_fault_distribution_v4/reset_only_rows.csv \
  --rejected-rows runs/m749_extreme_fault_distribution_v4/rejected_rows.csv \
  --seed-start 76000 \
  --seed-count 512 \
  --max-source-rows 512 \
  --horizons 2,4,6,8 \
  --device cpu \
  --run-dir runs/m752_v4_reset_source_sequence_intervention
```

M752 may run a small smoke first:

```text
seed_count: 64
max_source_rows: 64
horizons: 2,4
```

The smoke is only for schema and runtime validation.

## Claims Allowed

If M752 is outcome-positive, it may claim:

```text
sequence-level command-response interventions over v4 reset-sensitive extreme
fault rows create source-diverse outcome sensitivity.
```

It may not claim:

```text
trained driver improvement
PPO readiness
checkpoint promotion
true single-wheel fault physics
deployment-level generalization
```

If M752 is action-only, the next audit should decide between:

```text
four-wheel/high-fidelity dynamics
explicit yaw/disturbance fault model
stronger intervention variants
sequence objective only as a diagnostic shadow branch
```
