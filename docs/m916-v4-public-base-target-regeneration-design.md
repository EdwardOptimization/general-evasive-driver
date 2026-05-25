# M916 V4 Public-Base Target Regeneration Design

## Purpose

M916 starts the `v4_public_base_target_regeneration` branch.

The previous branch showed:

```text
M399 can reconstruct the old sequence corpus.
M399 can train a 128-dim residual head.
M755/M758/M761 targets do not produce an admissible normal-retaining residual.
Tail weighting moves low-tail metrics only after normal retention fails.
```

M916 is design-only:

```text
no training
no target generation execution
no M880 exact compatibility
no replay
no PPO
no checkpoint promotion
```

## Design Goal

The next implementation should regenerate targets from M399 behavior instead
of continuing to tune stale M568/M761 targets.

The target regeneration question:

```text
For M399 public-base low-tail states, can simulator-grounded local action
search find small action overrides that improve low-tail/terminal behavior
without requiring the large action drift that broke M914 normal retention?
```

This remains training-time data mining. It does not add rules to the deployable
actor.

## Inputs

M917 should use:

```text
base checkpoint:
  runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt

scenario config:
  configs/extreme_fault_distribution_v4_scenarios.json

source corpus:
  runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
  runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv

low-tail focus:
  runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv
  runs/m912_v4_public_base_sequence_recalibration_audit/group_deficit_summary.csv

diagnostic references:
  runs/m914_v4_public_base_tail_weighted_residual_probe/summary.json
  runs/m914_v4_public_base_tail_weighted_residual_probe/alpha_metrics.csv
```

M917 should treat M755/M758/M761 action targets as diagnostic lineage only. It
may use their metadata to reconstruct states, but not as primary target actions.

## Source Selection

M917 should focus first on the broad low-tail set:

```text
498 low-tail rows
17 fault-family pairs
variant: zero_command_obs
source_pool: m749_v4_reset_only
```

The implementation should cap work while preserving diversity:

```text
max_rows: 256
per_fault_family_pair_cap: 24
per_seed_cap: 4
horizon_values: 6 and 8
```

Selection priority:

```text
1. high gap_deficit;
2. low normal_intervention_gap;
3. source-diverse fault_family_pair coverage;
4. both horizon 6 and horizon 8 when available.
```

## Candidate Action Search

For each selected low-tail state, M917 should reconstruct the M399 snapshot and
evaluate a bounded local override set around the M399 base action:

```text
base_action = tanh(actor_mean(features))
```

Candidate deltas:

```text
steer_delta: [-0.08, -0.04, 0.04, 0.08]
brake_delta: [0.04, 0.08]
throttle_delta: [-0.08, -0.04, 0.04]
combined:
  steer_delta +/-0.04 with brake_delta +0.04
  steer_delta +/-0.08 with brake_delta +0.08
```

All candidate actions must be clipped to `[-1, 1]`. The search is a target
mining diagnostic, not a deploy-time rule policy.

## Acceptance Metrics

For every candidate override, M917 should compare against M399 base action
using the same reconstructed state/horizon metadata:

```text
action_l2_from_base
normal_intervention_gap_after
gap_deficit_after
low_tail_after
rollout_terminal_margin_delta
rollout_collision_delta
rollout_termination_delta
```

Primary accepted target:

```text
action_l2_from_base <= 0.08
gap_deficit_after <= gap_deficit_before - 0.004
normal_intervention_gap_after >= normal_intervention_gap_before + 0.004
low_tail_after == false
no worse collision / termination diagnostic if rollout is available
```

Fallback accepted target:

```text
action_l2_from_base <= 0.12
gap_deficit_after <= gap_deficit_before - 0.006
low_tail_after == false
rollout_terminal_margin_delta >= 0
```

Rows outside these gates should be written as rejected target rows, not silently
dropped.

## Diversity Gates

M917 should pass only if accepted targets are broad enough:

```text
accepted_targets >= 80
distinct_fault_family_pairs >= 8
distinct_seeds >= 24
accepted_horizon_values includes 6 and 8
max_fault_family_pair_fraction <= 0.25
```

If these gates fail, route to scenario expansion or source mining, not residual
training.

## Required Outputs

M917 should write:

```text
runs/m917_v4_public_base_target_regeneration/summary.json
runs/m917_v4_public_base_target_regeneration/selected_source_rows.csv
runs/m917_v4_public_base_target_regeneration/candidate_action_rows.csv
runs/m917_v4_public_base_target_regeneration/accepted_target_rows.csv
runs/m917_v4_public_base_target_regeneration/rejected_target_rows.csv
runs/m917_v4_public_base_target_regeneration/group_acceptance_summary.csv
```

The accepted target rows should include:

```text
contrast_group_id
source_index
seed
step
preferred_fault
preferred_fault_family
wrong_fault_family
fault_family_pair
variant
horizon
base_steer
base_throttle
base_brake
target_steer
target_throttle
target_brake
action_l2_from_base
gap_before
gap_after
gap_deficit_before
gap_deficit_after
low_tail_after
acceptance_class
```

## Next Route

If M917 passes diversity and acceptance gates:

```text
route to public-base regenerated-target residual objective design
```

If M917 produces too few accepted targets:

```text
route to public-base source expansion design
```

If accepted targets are concentrated in one fault family:

```text
route to source-diversity expansion design
```

## Safeguards

M917 must not:

```text
train a residual head;
update actor parameters;
run M880 exact compatibility;
run replay;
run PPO;
promote a checkpoint;
claim target mining success as driver improvement.
```

## Supported Claims

M916 supports:

```text
1. The next route should regenerate M399-rooted targets, not tune stale target
   weights.
2. Target regeneration should be source-diverse and action-drift bounded.
3. Accepted targets must be backed by deficit and low-tail improvements.
```

## Unsupported Claims

M916 does not support:

```text
target regeneration success;
residual objective success;
M880 exact compatibility;
replay retention;
PPO safety;
checkpoint promotion.
```

## Decision

Decision:

```text
public_base_target_regeneration_design_admit_m917
```

Next:

```text
m917-v4-public-base-target-regeneration-implementation
```

M917 should implement and run no-training M399-rooted target regeneration.
