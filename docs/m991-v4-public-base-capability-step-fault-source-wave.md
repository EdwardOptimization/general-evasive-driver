# M991 V4 Public Base Capability-Step Fault Source Wave

## Purpose

M991 scales the M990 capability-step smoke into a larger no-training source
wave.

Question:

```text
Does the sparse M990 wrong-history signal repeat across more seeds, snapshots,
and fault-family pairs?
```

M991 creates:

```text
configs/m991_capability_step_fault_source_wave.json
```

from the M990 config, increasing source coverage while keeping the same
current-model/proxy fault semantics.

M991 does not train, run PPO, promote, use private holdout, or change actor
inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --config configs/m991_capability_step_fault_source_wave.json \
  --pairing-mode cross_fault \
  --seed-start 99100 \
  --seed-count 256 \
  --device auto \
  --run-dir runs/m991_v4_public_base_capability_step_fault_source_wave
```

## Result

```text
result_class: cross_fault_reset_only
scenario_count: 3328
snapshot_count: 16393
matched_pair_count: 4096
unmatched_rows: 1
accepted_rows: 0
reset_only_rows: 1380
rejected_rows: 2716
normal_failed_rejected: 732
history_insensitive_rejected: 1984
wrong_history_action_critical_rows: 0
reset_history_action_critical_rows: 1380
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

M991 passes as a no-training source wave and falsifies the optimistic
interpretation of M990:

```text
M990's two accepted wrong-history rows do not repeat under fresh larger coverage.
```

## Source Coverage

The source wave covers broad fault-family pair groups:

| Fault pair | Rows | Reset-only rows | Unique seeds |
| --- | ---: | ---: | ---: |
| brake_authority_drop -> global_mu_drop | 629 | 203 | 69 |
| global_mu_drop -> brake_authority_drop | 391 | 151 | 69 |
| combined_fault -> front_lateral_authority_drop | 333 | 115 | 69 |
| rear_lateral_authority_drop -> drive_authority_drop | 342 | 181 | 69 |
| mass_cg_shift -> brake_authority_drop | 342 | 158 | 69 |
| steering_fault -> front_lateral_authority_drop | 288 | 49 | 69 |

The source wave is not pair-starved. The absence of accepted rows is therefore
not explained by missing matched pairs.

## Reset-Only Interpretation

M991 has strong reset-hidden sensitivity:

```text
reset_only_rows: 1380
reset_history_action_critical_rows: 1380
```

But wrong-history sensitivity is absent:

```text
accepted_rows: 0
wrong_history_action_critical_rows: 0
```

This means the recurrent state matters, but the current cross-fault hidden
injection is not producing an incompatible enough capability belief to damage
the continuation.

The typical reset-only row has:

```text
wrong-history margin gap: near zero
reset-hidden margin gap: positive and above threshold
wrong-history first-action gap: often near zero
reset-hidden first-action gap: large
```

So reset-hidden is acting as a disruption/intervention, while wrong-history is
not yet a clean belief-mismatch intervention.

## Supported Claims

```text
Capability-step fault events produce broad matched-pair artifacts on M974.
Reset-hidden recurrent-state sensitivity is strong under these events.
The current P0 actor contract remains intact.
No training, PPO, or promotion occurred.
```

## Falsified Claims

```text
M990's sparse wrong-history rows are already repeatable.
The current cross-fault hidden matching is enough to produce source-diverse
wrong-history outcome sensitivity.
The branch is ready for objective training or PPO.
```

## Failure Taxonomy

```text
scenario_sampling_failure
metric_artifact
```

`scenario_sampling_failure` because the larger source wave still yields zero
wrong-history accepted rows.

`metric_artifact` because counting the 1380 reset-only rows as self-ID proof
would overclaim the evidence.

## Decision

Do not train. Do not run PPO. Do not promote. Do not export a wrong-history
objective corpus from M991.

Admit a reset-only audit / sequence-intervention design:

```text
m992-v4-public-base-capability-step-reset-only-audit
```

M992 should determine whether the next route is:

```text
1. sequence-level wrong-history intervention;
2. stronger action-response mismatch intervention;
3. retargeted fault-pair generation;
4. or a simulator/dynamics extension for asymmetric faults.
```

## Artifacts

```text
configs/m991_capability_step_fault_source_wave.json
runs/m991_v4_public_base_capability_step_fault_source_wave/summary.json
runs/m991_v4_public_base_capability_step_fault_source_wave/scenario_summary.csv
runs/m991_v4_public_base_capability_step_fault_source_wave/fault_family_summary.csv
runs/m991_v4_public_base_capability_step_fault_source_wave/fault_family_pair_summary.csv
runs/m991_v4_public_base_capability_step_fault_source_wave/severity_summary.csv
runs/m991_v4_public_base_capability_step_fault_source_wave/severity_pair_summary.csv
runs/m991_v4_public_base_capability_step_fault_source_wave/cross_fault_pair_summary.csv
runs/m991_v4_public_base_capability_step_fault_source_wave/matched_hidden_condition_pairs.csv
runs/m991_v4_public_base_capability_step_fault_source_wave/matched_cross_fault_pairs.csv
runs/m991_v4_public_base_capability_step_fault_source_wave/intervention_rollouts.csv
runs/m991_v4_public_base_capability_step_fault_source_wave/accepted_rows.csv
runs/m991_v4_public_base_capability_step_fault_source_wave/reset_only_rows.csv
runs/m991_v4_public_base_capability_step_fault_source_wave/rejected_rows.csv
runs/m991_v4_public_base_capability_step_fault_source_wave/model_fidelity_limits.md
```
