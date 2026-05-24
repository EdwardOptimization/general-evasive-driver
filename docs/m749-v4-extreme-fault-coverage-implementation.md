# M749 V4 Extreme-Fault Coverage Implementation

## Purpose

M749 runs the no-training v4 extreme-fault source-mining wave designed in M748.

The question is:

```text
Does broader v4 fault coverage produce reset, wrong-history action, or
outcome-sensitive command-response source rows beyond the v3 wave?
```

This is a diagnostic data wave only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Registered Run

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v4_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 76000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m749_extreme_fault_distribution_v4
```

Run directory:

```text
runs/m749_extreme_fault_distribution_v4
```

## Result

Summary:

```text
result_class: cross_fault_reset_only

fault_count: 28
future_only_fault_count: 14
scenario_count: 14848
snapshot_count: 100624
matched_pair_count: 12288
unmatched_rows: 32

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
```

M749 successfully broadened source generation:

```text
scenario_count >= 12000: pass
matched_pair_count >= 10000: pass
future_only_fault_count == 14: pass
actor/training safety: pass
```

It still did not produce wrong-history source rows:

```text
wrong_history_action_critical_rows: 0
accepted_rows: 0
```

It produced a larger reset-history source surface than v3:

```text
M740 reset_only_rows: 744
M749 reset_only_rows: 1171
```

## Reset Surface Diversity

The reset-only surface contains:

```text
reset_only_rows: 1171
unique reset seeds: 27
unique preferred fault families: 9
unique wrong fault families: 6
unique fault-family pairs: 17
max reset seed share: 0.139197
max preferred family share: 0.310845
max wrong family share: 0.349274
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

The surface is useful but not perfectly balanced:

```text
train rows: 1078
heldout rows: 93
```

So a follow-up sequence-intervention source adapter should source-balance by
seed, preferred family, wrong family, and fault-family pair, rather than using
all reset rows directly.

## Interpretation

M749 supports the coverage-mining hypothesis:

```text
v4 coverage produces more reset-sensitive source rows than v3.
```

But it also repeats the key M740 pattern:

```text
broader cross-fault coverage alone does not make wrong-history action-critical
rows appear under the current one-step cross-fault metric.
```

This is not a runner or config failure:

```text
v4 config loaded
current-model families are supported
future-only faults are recorded as metadata
actor checksum stayed fixed
no optimizer or PPO ran
```

The blocker is now specific:

```text
The v4 reset surface must be tested with persistent sequence-level
command-response interventions, because M743 already showed that sequence
intervention can convert reset-only source rows into outcome-sensitive rows.
```

## Failure Taxonomy

Primary:

```text
scenario_sampling_failure
metric_artifact
```

Reason:

```text
The v4 source distribution is broad and technically valid, but the selected
cross-fault wrong-history metric still produces `0` wrong-history
action-critical rows. The `1171` reset-only rows are real recurrent evidence,
but not the stronger wrong-history self-ID claim.
```

Not present:

```text
contract_violation
proof_washout
training_instability
promotion_gate_failure
private_holdout_contamination
```

## Artifacts

```text
runs/m749_extreme_fault_distribution_v4/summary.json
runs/m749_extreme_fault_distribution_v4/scenario_summary.csv
runs/m749_extreme_fault_distribution_v4/snapshot_candidates.csv
runs/m749_extreme_fault_distribution_v4/matched_hidden_condition_pairs.csv
runs/m749_extreme_fault_distribution_v4/matched_cross_fault_pairs.csv
runs/m749_extreme_fault_distribution_v4/intervention_rollouts.csv
runs/m749_extreme_fault_distribution_v4/accepted_rows.csv
runs/m749_extreme_fault_distribution_v4/reset_only_rows.csv
runs/m749_extreme_fault_distribution_v4/rejected_rows.csv
runs/m749_extreme_fault_distribution_v4/fault_family_summary.csv
runs/m749_extreme_fault_distribution_v4/fault_family_pair_summary.csv
runs/m749_extreme_fault_distribution_v4/model_fidelity_limits.md
```

## Next Decision

M750 should audit M749 before any objective design.

Expected next branch if the audit agrees:

```text
v4 reset-source sequence intervention
```

Rationale:

```text
M740 -> M743 already showed that reset-only source rows can become
sequence-outcome positives when persistent command-response interventions are
used. M749 produces an even larger reset source surface, so the next test should
apply the same sequence-level intervention logic to v4.
```
