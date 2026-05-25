# M918 V4 Public-Base Target Source Expansion Design

## Purpose

M918 designs the next source route after M917 failed the target-regeneration
diversity gate.

M917 showed:

```text
selected_sources_reconstructed: 67
accepted_targets: 67
rejected_targets: 0
distinct_seeds: 19
max_fault_family_pair_fraction: 0.3582089552238806
```

The strict M912 low-tail input has only `21` distinct seeds, so the M917
`distinct_seeds >= 24` gate cannot be met from strict low-tail rows alone.

M918 is design-only:

```text
no target generation execution
no residual-head training
no M880 exact compatibility
no replay
no PPO
no checkpoint promotion
```

## Design Goal

M919 should expand the source pool without weakening the actor contract or
turning target mining into a deployed rule.

The next question is:

```text
Can a source-balanced near-tail candidate pool provide enough M399-rooted
target rows for regenerated-target residual objective design?
```

This is still data infrastructure. It does not claim a better driver.

## Inputs

M919 should use:

```text
base checkpoint:
  runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt

scenario config:
  configs/extreme_fault_distribution_v4_scenarios.json

full source corpus:
  runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
  runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv

near-base M399 objective metrics:
  runs/m909_v4_public_base_residual_head_probe/objective_rows.csv

strict low-tail labels:
  runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv
  runs/m912_v4_public_base_sequence_recalibration_audit/group_deficit_summary.csv

M917 diagnostic target output:
  runs/m917_v4_public_base_target_regeneration/summary.json
  runs/m917_v4_public_base_target_regeneration/accepted_target_rows.csv
```

## Source Expansion

M919 should build an expanded candidate set from M909 near-base alpha `0.02`
rows, joined to M912 low-tail membership by:

```text
contrast_group_id
source_index
variant
horizon
```

Rows are eligible if they satisfy either:

```text
strict_low_tail == true
```

or a near-tail coverage condition:

```text
gap_deficit >= 0.012
or normal_intervention_gap <= 0.030
```

The near-tail rows are not proof rows. They are included only to create a
source-diverse training target pool after M917 proved the strict pool cannot
satisfy seed coverage.

## Selection Discipline

M919 should use a coverage-first selector:

```text
max_rows: 256
per_fault_family_pair_cap: 24
per_seed_soft_cap: 8
min_seed_coverage_before_second_pass: 24
minimum_strict_low_tail_rows: 60
```

Selection order:

```text
1. include strict low-tail rows with high gap_deficit and low
   normal_intervention_gap;
2. add near-tail rows from seeds missing in strict low-tail membership;
3. add underrepresented fault-family pairs;
4. fill remaining capacity with highest-deficit near-tail rows subject to pair
   caps.
```

The selector should export both accepted and rejected source-candidate rows so
future audits can distinguish source scarcity from action-target scarcity.

## Target Search

M919 should reuse the M917 bounded action-delta search around the M399 base
action. For strict low-tail rows, keep the M917 primary acceptance rule:

```text
action_l2_from_base <= 0.08
gap_deficit_after <= gap_deficit_before - 0.004
normal_intervention_gap_after >= normal_intervention_gap_before + 0.004
low_tail_after == false
```

For near-tail coverage rows, acceptance should require:

```text
action_l2_from_base <= 0.08
normal_intervention_gap_after >= normal_intervention_gap_before + 0.004
gap_deficit_after <= gap_deficit_before
low_tail_after == false
```

Near-tail rows should carry `source_label=near_tail_coverage` so later
residual training can weight strict low-tail and near-tail rows separately.

## Pass Gates

M919 should pass only if:

```text
accepted_targets >= 96
strict_low_tail_accepted_targets >= 60
distinct_fault_family_pairs >= 10
distinct_seeds >= 24
accepted_horizon_values includes 6 and 8
max_fault_family_pair_fraction <= 0.25
actor_parameters_changed == false
training_started == false
replay_used == false
ppo_used == false
promoted == false
```

If these gates fail, do not train a residual head.

## Required Outputs

M919 should write:

```text
runs/m919_v4_public_base_expanded_target_regeneration/summary.json
runs/m919_v4_public_base_expanded_target_regeneration/source_candidate_rows.csv
runs/m919_v4_public_base_expanded_target_regeneration/rejected_source_candidate_rows.csv
runs/m919_v4_public_base_expanded_target_regeneration/selected_source_rows.csv
runs/m919_v4_public_base_expanded_target_regeneration/candidate_action_rows.csv
runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv
runs/m919_v4_public_base_expanded_target_regeneration/rejected_target_rows.csv
runs/m919_v4_public_base_expanded_target_regeneration/group_acceptance_summary.csv
```

The summary should include:

```text
strict_low_tail_input_rows
near_tail_candidate_rows
expanded_source_candidates
selected_sources
selected_strict_low_tail_sources
selected_near_tail_sources
accepted_targets
strict_low_tail_accepted_targets
near_tail_accepted_targets
distinct_fault_family_pairs
distinct_seeds
max_fault_family_pair_fraction
actor_parameters_changed
training_started
m880_exact_used
replay_used
ppo_used
promoted
result_class
```

## Route Decision

If M919 passes:

```text
route to regenerated-target residual objective design
```

If M919 fails because accepted targets are still sparse:

```text
route to M399 public-base source refresh from a larger no-training sequence
intervention wave
```

If M919 fails because source concentration remains high:

```text
route to stronger source-balanced selection or new seed/fault-family sampling
```

## Safeguards

M919 must not:

```text
train;
update actor parameters;
run M880 exact compatibility;
run replay;
run PPO;
promote a checkpoint;
claim that target mining improves closed-loop driving.
```

## Decision

Decision:

```text
public_base_target_source_expansion_design_admit_m919
```

Next:

```text
m919-v4-public-base-expanded-target-regeneration-implementation
```
