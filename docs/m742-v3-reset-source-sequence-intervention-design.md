# M742 V3 Reset-Source Sequence Intervention Design

## Purpose

M742 designs the next no-training experiment after M741 audited M740 as a broad
`cross_fault_reset_only` result.

The question is:

```text
Can M740's reset-history-sensitive v3 source surface become outcome-sensitive
when command-response interventions persist over a short sequence?
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

M740 broadened extreme-fault coverage:

```text
scenario_count: 16896
matched_pair_count: 8192
reset_only_rows: 744
wrong_history_action_critical_rows: 0
```

M741 audited that as:

```text
coverage is broad enough to produce recurrent-state sensitivity,
but the current cross-fault wrong-history swap is still not the right control
variable for deployed action or outcome evidence.
```

M734 already showed the useful pattern:

```text
one-step or reset-only evidence can become outcome-sensitive when the
command-response intervention persists for H steps.
```

So M742 should not run PPO. It should design a source-balanced M743 sequence
intervention over M740 reset-only rows.

## Source Rows

Primary source:

```text
runs/m740_extreme_fault_distribution_v3/reset_only_rows.csv
```

Available reset source surface:

```text
rows: 744
unique seeds: 21
unique preferred fault families: 9
unique wrong fault families: 8
unique preferred severities: 4
unique wrong severities: 4
max seed dominance: 0.142473
max preferred family dominance: 0.202957
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
runs/m740_extreme_fault_distribution_v3/rejected_rows.csv
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

The current M740 rejected rows provide enough candidate sentinels under this
rule:

```text
sentinel candidates: 242
unique sentinel seeds: 14
```

## Source Adapter

M743 needs a dedicated adapter because M740 rows are not in the same schema as
M734 source rows.

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
normal_margin
match_distance
pairing_rule
```

For M740 rows, `fault_family_pair` should be reconstructed from
`preferred_fault_family` and `wrong_fault_family` because M740 reset rows do not
store that column directly.

The source adapter should not alter actor observations. Hidden fault names and
families remain logging/source-selection metadata only.

## Source Balance

Initial M743 source targets:

```text
max_source_rows: 512
sentinel_fraction: 0.10
primary target: about 461
sentinel target: about 51
```

Balance keys:

```text
source_role
seed
preferred_fault_family
wrong_fault_family
fault_family_pair
preferred_fault_severity
wrong_fault_severity
assigned_split
step_bucket
normal_margin_bucket
reset_action_l2_bucket
reset_margin_gap_bucket
pairing_rule
```

Registered source gates:

```text
source_candidate_rows >= 512 if enough rows exist, otherwise classify
source_unique_seeds >= 16
source_unique_preferred_fault_families >= 7
source_unique_wrong_fault_families >= 6
source_unique_fault_family_pairs >= 16
source_max_seed_dominance <= 0.16
source_max_preferred_family_dominance <= 0.25
sentinel_fraction between 0.05 and 0.15
```

The `0.16` seed-dominance cap is intentional: M740 reset rows have only `21`
unique seeds and max dominance `0.142473`, so the source gate should enforce
balance without making the branch impossible before it starts.

## Intervention Semantics

M743 should reuse the M734 sequence intervention semantics:

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
```

Optional if cheap and reconstructable:

```text
command_shift_obs_H
wrong_cross_fault_hidden_H
```

The first M743 wave should prioritize the M734-positive variants:

```text
zero_command_obs_H
reset_hidden_each_step_H
```

But it may include `command_shift_obs_H` and `response_delay_obs_H` for
continuity with M734 diagnostics.

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
sequence_action_critical_rows >= 300
unique_sequence_action_seeds >= 10
```

Sequence outcome gate:

```text
sequence_outcome_critical_rows >= 20
unique_sequence_outcome_seeds >= 8
unique_sequence_outcome_fault_family_pairs >= 4
max_sequence_outcome_seed_dominance <= 0.25
sentinel_false_positive_rate <= 0.05
normal_history_retention_pass == true
actor_parameters_changed == false
```

Failure classes:

```text
v3_reset_sequence_outcome_positive
v3_reset_sequence_action_only
v3_reset_source_balance_blocked
v3_reset_sequence_artifact
v3_reset_sequence_neutral
```

## M743 Command

Registered implementation command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v3_reset_source_sequence_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v3_scenarios.json \
  --reset-rows runs/m740_extreme_fault_distribution_v3/reset_only_rows.csv \
  --rejected-rows runs/m740_extreme_fault_distribution_v3/rejected_rows.csv \
  --seed-start 73000 \
  --seed-count 512 \
  --max-source-rows 512 \
  --horizons 2,4,6,8 \
  --device cpu \
  --run-dir runs/m743_v3_reset_source_sequence_intervention
```

M743 may run a small smoke first:

```text
seed_count: 64
max_source_rows: 64
horizons: 2,4
```

The smoke is only for schema and runtime validation.

## Claims Allowed

If M743 is outcome-positive, it may claim:

```text
sequence-level command-response interventions over v3 reset-sensitive extreme
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

If M743 is action-only, the next audit should decide between:

```text
simulator fidelity / four-wheel dynamics
explicit yaw/disturbance fault model
observation/architecture changes
sequence objective only as a diagnostic shadow branch
```
