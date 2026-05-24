# M741 Extreme-Fault Distribution V3 Audit

## Purpose

M741 audits the M740 v3 extreme-fault wave before any further data generation,
objective design, or PPO.

The question is:

```text
Did broader extreme-fault coverage solve the self-ID evidence blocker, or does
the next branch need to convert v3 reset-history sensitivity into sequence-level
outcome evidence?
```

This audit is process-only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M740 generated:

```text
scenario_count: 16896
snapshot_count: 96715
matched_pair_count: 8192
unmatched_rows: 7
future_only_fault_count: 12

accepted_rows: 0
reset_only_rows: 744
rejected_rows: 7448
normal_failed_rejected: 2233
history_insensitive_rejected: 5215

history_action_critical_rows: 744
wrong_history_action_critical_rows: 0
reset_history_action_critical_rows: 744

actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
result_class: cross_fault_reset_only
```

Reset-only diversity:

```text
reset_only_rows: 744
unique_reset_seeds: 21
unique_preferred_fault_families: 9
unique_wrong_fault_families: 8
unique_preferred_severities: 4
unique_wrong_severities: 4
max_reset_seed_dominance: 0.142473
max_preferred_family_dominance: 0.202957
```

Top preferred families:

```text
front_lateral_authority_drop: 151
combined_fault: 144
mass_cg_shift: 89
global_mu_drop: 83
drive_authority_drop: 76
steering_fault: 74
brake_authority_drop: 54
delay_noise_fault: 48
```

## Supported Claims

M741 supports:

```text
1. The v3 extreme-fault distribution broadened source generation substantially:
   16896 scenarios and 8192 matched pairs.

2. The current actor has real recurrent-state sensitivity on v3 extreme faults:
   744 reset-history action-critical rows.

3. Coverage alone did not make the current cross-fault wrong-history
   intervention produce deployed-action evidence.

4. The v3 reset-only surface is broad enough to justify a source-balanced
   sequence-level command-response intervention design.
```

## Falsified Claims

M741 falsifies:

```text
1. Broader v3 coverage by itself is enough to produce wrong-history
   action-critical rows under the current cross-fault hidden swap metric.

2. M740 should be used directly for PPO, objective design, or checkpoint
   promotion.

3. Reset-only rows can be reported as wrong-history self-identification proof.
```

M741 does not falsify:

```text
1. The command-response-history dependence hypothesis.

2. The value of broader extreme-fault coverage.

3. The possibility that sequence-level interventions on v3 reset rows will
   produce outcome-sensitive rows, as M734 did on M731 rows.
```

## Failure Taxonomy Summary

Primary:

```text
scenario_sampling_failure
metric_artifact
```

Reason:

```text
The v3 source wave is broad and technically clean, but the current metric
continues to produce reset-only rows. Cross-fault wrong-history swapping is not
the right next control variable for this source surface.
```

Not present:

```text
contract_violation
proof_washout
training_instability
promotion_gate_failure
private_holdout_contamination
```

## Public Gate Overfit Risk

The public-gate overfit risk is moderate.

Reasons:

```text
1. M740 is a public diagnostic wave.
2. The reset rows cover only 21 seeds despite 744 rows.
3. The row surface is broad by fault family but not yet source-balanced enough
   for objective work.
```

Mitigation:

```text
M742 should be design-only and should require source-balanced selection from
M740 reset rows before running sequence interventions.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch: v3_reset_source_sequence_intervention
```

Rationale:

```text
M734 showed that sequence-level command-response intervention can convert
action-only history sensitivity into outcome evidence. M740 now provides a much
larger v3 reset-history action-sensitive source surface.
```

M742 should not train. It should design a no-training sequence-level
intervention branch over M740 reset-only rows.

## M742 Requirements

M742 should design:

```text
source adapter:
  convert M740 reset_only_rows.csv into source rows with source_index,
  source_role, preferred/wrong fault metadata, step, split, severity, and
  pairing rule.

source balance:
  cap per seed
  cap per preferred family
  cap per wrong family
  preserve severity and split diversity
  include sentinel rows from low reset_action_l2_gap or healthy margin rows

intervention variants:
  normal
  zero_command_obs_H
  response_delay_obs_H
  reset_hidden_then_normal_H
  reset_hidden_each_step_H
  optional wrong_cross_fault_hidden_H only if reconstructable

horizons:
  H in {2, 4, 6, 8}

gates:
  source rows >= 512 if available
  unique seeds >= 16
  preferred families >= 7
  wrong families >= 6
  sequence action rows >= 300
  sequence outcome rows >= 20
  sentinel false-positive rate <= 0.05
  actor checksum unchanged
```

If M742/M743 again produces reset/action-only evidence without outcome rows,
then simulator fidelity or a more explicit disturbance/four-wheel model should
move up in priority. For now, sequence intervention is the more direct next
test.
