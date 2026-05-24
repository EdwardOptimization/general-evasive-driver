# M740 Extreme-Fault Distribution V3 Implementation

## Purpose

M740 runs the no-training v3 extreme-fault data wave designed in M739.

The question is:

```text
Does broader extreme-fault coverage produce source-diverse wrong-history or
outcome-sensitive self-ID rows beyond the fixed M737 public corpus?
```

This is a diagnostic data wave only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Config Smoke

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v3_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 73000 \
  --seed-count 1 \
  --device cpu \
  --run-dir runs/m740_extreme_fault_distribution_v3_smoke
```

Smoke result:

```text
scenario_count: 33
snapshot_count: 198
matched_pair_count: 192
unmatched_rows: 0
reset_only_rows: 3
wrong_history_action_critical_rows: 0
reset_history_action_critical_rows: 3
future_only_fault_count: 12
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
result_class: cross_fault_reset_only
```

The smoke validated config loading and artifact schema. It is not used as a
capability claim.

## Registered Run

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_distribution_v3_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 73000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m740_extreme_fault_distribution_v3
```

Run directory:

```text
runs/m740_extreme_fault_distribution_v3
```

## Result

Summary:

```text
result_class: cross_fault_reset_only

fault_count: 32
future_only_fault_count: 12
scenario_count: 16896
snapshot_count: 96715
matched_pair_count: 8192
unmatched_rows: 7

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
```

M740 successfully broadened source coverage:

```text
scenario_count >= 16000: pass
matched_pair_count >= 4096: pass
future_only_fault_count >= 10: pass
actor/training safety: pass
```

But it did not produce wrong-history source rows:

```text
wrong_history_action_critical_rows: 0
accepted_rows: 0
```

It produced a large reset-history source surface:

```text
reset_only_rows: 744
reset_history_action_critical_rows: 744
```

## Interpretation

The user's coverage hypothesis was tested directly.

M740 supports:

```text
The previous distribution was not the only issue; broadening to v3 creates many
reset-history-sensitive cases, but cross-fault wrong-history intervention still
does not reach deployed-action criticality.
```

This is not a simulator or config failure:

```text
v3 config loaded
source generation scale passed
future-only boundary is recorded
actor checksum stayed fixed
no optimizer or PPO ran
```

The new blocker is more specific:

```text
current cross-fault wrong-history swap remains too weak or too misaligned with
the actor's deployed action path, while reset/sequence-style history removal
does expose strong action sensitivity.
```

This matches the earlier pattern:

```text
M716: broader v2 coverage -> reset-only
M728/M731: source-balanced action rows -> one-step outcome sparse
M734: sequence-level command-response intervention -> outcome positive
M740: broader v3 coverage -> reset-only at cross-fault level
```

So the next step should not be PPO. It should audit whether M740's 744 reset
rows are a good source surface for sequence-level interventions.

## Failure Taxonomy

Primary:

```text
scenario_sampling_failure
metric_artifact
```

Reason:

```text
The v3 source distribution is broad and technically valid, but the selected
cross-fault wrong-history metric still produces 0 wrong-history action-critical
rows. The reset-only rows are real recurrent evidence but not the stronger
wrong-history self-ID claim.
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
runs/m740_extreme_fault_distribution_v3/summary.json
runs/m740_extreme_fault_distribution_v3/scenario_summary.csv
runs/m740_extreme_fault_distribution_v3/snapshot_candidates.csv
runs/m740_extreme_fault_distribution_v3/matched_hidden_condition_pairs.csv
runs/m740_extreme_fault_distribution_v3/matched_cross_fault_pairs.csv
runs/m740_extreme_fault_distribution_v3/intervention_rollouts.csv
runs/m740_extreme_fault_distribution_v3/accepted_rows.csv
runs/m740_extreme_fault_distribution_v3/reset_only_rows.csv
runs/m740_extreme_fault_distribution_v3/rejected_rows.csv
runs/m740_extreme_fault_distribution_v3/fault_family_summary.csv
runs/m740_extreme_fault_distribution_v3/fault_family_pair_summary.csv
runs/m740_extreme_fault_distribution_v3/model_fidelity_limits.md
```

## Next Decision

M741 should audit before any new implementation.

The likely next branch is:

```text
v3 reset-source sequence-level command-response intervention
```

Rationale:

```text
M734 already showed that sequence-level command/history corruption can convert
action-only evidence into outcome evidence. M740 now supplies a much broader
reset-history source surface.
```

PPO, actor updates, objective design, and checkpoint promotion remain blocked.
