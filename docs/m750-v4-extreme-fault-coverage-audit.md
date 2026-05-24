# M750 V4 Extreme-Fault Coverage Audit

## Purpose

M750 audits the M749 v4 extreme-fault source-mining wave before any further
data generation, objective design, or PPO.

The question is:

```text
Did v4 coverage solve the self-ID evidence blocker, or should the next branch
convert v4 reset-history sensitivity into sequence-level outcome evidence?
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

M749 generated:

```text
scenario_count: 14848
snapshot_count: 100624
matched_pair_count: 12288
unmatched_rows: 32
fault_count: 28
future_only_fault_count: 14

accepted_rows: 0
reset_only_rows: 1171
rejected_rows: 11117
normal_failed_rejected: 4666
history_insensitive_rejected: 6451

history_action_critical_rows: 1171
wrong_history_action_critical_rows: 0
reset_history_action_critical_rows: 1171

actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
result_class: cross_fault_reset_only
```

Reset-only diversity:

```text
reset_only_rows: 1171
unique_reset_seeds: 27
unique_preferred_fault_families: 9
unique_wrong_fault_families: 6
unique_fault_family_pairs: 17
max_reset_seed_share: 0.139197
max_preferred_family_share: 0.310845
max_wrong_family_share: 0.349274
```

Top reset fault-family pairs:

```text
combined_fault->global_mu_drop: 327
front_lateral_authority_drop->combined_fault: 205
mass_cg_shift->front_lateral_authority_drop: 141
global_mu_drop->front_lateral_authority_drop: 113
brake_authority_drop->global_mu_drop: 82
steering_fault->front_lateral_authority_drop: 78
drive_authority_drop->rear_lateral_authority_drop: 52
```

Sentinel availability under the M742-style history-insensitive rule:

```text
sentinel candidates: 361
unique sentinel seeds: 23
```

## Supported Claims

M750 supports:

```text
1. V4 coverage broadened source generation and reset-history evidence:
   M740 reset_only_rows: 744
   M749 reset_only_rows: 1171

2. The v4 config is technically valid for the current runner:
   28 executable current/proxy fault specs, 26 pairing rules, 14 future-only
   fault labels, and no actor mutation.

3. The current actor has recurrent-state sensitivity on a broader v4 extreme
   fault surface.

4. The v4 reset-only surface is broad enough to justify a source-balanced
   sequence-level command-response intervention design.
```

## Falsified Claims

M750 falsifies:

```text
1. Broader v4 current/proxy coverage by itself is enough to produce
   wrong-history action-critical rows under the current cross-fault hidden swap.

2. M749 should be used directly for PPO, objective design, or checkpoint
   promotion.

3. Reset-only rows can be reported as wrong-history self-identification proof.
```

M750 does not falsify:

```text
1. The command-response-history dependence hypothesis.

2. The value of broader extreme-fault coverage.

3. The possibility that sequence-level interventions on v4 reset rows will
   produce outcome-sensitive rows, as M743 did on M740 reset rows.
```

## Failure Taxonomy Summary

Primary:

```text
scenario_sampling_failure
metric_artifact
```

Reason:

```text
The v4 source wave is broad and technically clean, but the current cross-fault
wrong-history metric continues to produce reset-only rows. Cross-fault hidden
swap is not the right next control variable for this source surface.
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
1. M749 is a public diagnostic wave.
2. Reset rows cover only 27 seeds despite 1171 rows.
3. Preferred and wrong family shares are concentrated.
4. The rows are still reset/action evidence, not outcome evidence.
```

Mitigation:

```text
M751 should be design-only and should require source-balanced selection from
M749 reset rows before running sequence interventions.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch: v4_reset_source_sequence_intervention
```

Rationale:

```text
M743 showed that sequence-level command-response intervention can convert
M740 reset-only source rows into outcome-sensitive rows. M749 now provides a
larger v4 reset-history action-sensitive source surface. The next direct test is
therefore a source-balanced v4 sequence intervention, not PPO.
```

## M751 Requirements

M751 should design:

```text
source adapter:
  convert M749 reset_only_rows.csv into source rows with v4 metadata,
  source_index, source_role, preferred/wrong fault metadata, step, split,
  severity, reset gaps, pairing rule, and claim-boundary fields.

source balance:
  cap per seed
  cap per preferred family
  cap per wrong family
  cap per fault-family pair
  preserve severity and split diversity
  include sentinel rows from history-insensitive rejected rows

intervention variants:
  normal
  zero_command_obs_H
  response_delay_obs_H
  reset_hidden_then_normal_H
  reset_hidden_each_step_H
  command_response_mismatch_H if reconstructable

horizons:
  H in {2, 4, 6, 8}

gates:
  source rows >= 512 if available
  unique seeds >= 18
  preferred families >= 8
  wrong families >= 5
  fault-family pairs >= 14
  sequence action rows >= 400
  sequence outcome rows >= 40
  sentinel false-positive rate <= 0.05
  actor checksum unchanged
```

If M751/M752 produces action-only evidence without outcome rows, then the
project should consider a four-wheel/high-fidelity or explicit-disturbance
branch. For now, sequence intervention is the next most direct and already
validated test.
