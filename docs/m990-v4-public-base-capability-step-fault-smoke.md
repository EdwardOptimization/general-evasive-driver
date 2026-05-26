# M990 V4 Public Base Capability-Step Fault Smoke

## Purpose

M990 runs the minimal no-training smoke admitted by M989.

Current public-gate base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

M990 creates:

```text
configs/m990_capability_step_fault_scenarios.json
```

and runs the existing hidden-fault event harness:

```text
src/autodrift/extreme_dynamics_scenario_corpus.py
```

This milestone does not train, run PPO, promote, use private holdout, or change
actor inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --config configs/m990_capability_step_fault_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 99000 \
  --seed-count 64 \
  --device auto \
  --run-dir runs/m990_v4_public_base_capability_step_fault_smoke
```

## Result

```text
result_class: cross_fault_wrong_sparse
scenario_count: 832
snapshot_count: 3289
matched_pair_count: 768
unmatched_rows: 0
accepted_rows: 2
reset_only_rows: 132
rejected_rows: 634
normal_failed_rejected: 257
history_insensitive_rejected: 377
wrong_history_action_critical_rows: 2
reset_history_action_critical_rows: 132
unique_accepted_fault_families: 1
unique_accepted_wrong_fault_families: 1
unique_accepted_severities: 1
unique_accepted_seeds: 1
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

M990 passes as an infrastructure smoke:

```text
summary.json exists
scenario_summary.csv exists
matched_cross_fault_pairs.csv exists
intervention_rollouts.csv exists
model_fidelity_limits.md exists
matched_pair_count > 0
actor checksum unchanged
```

## Accepted Rows

The two accepted wrong-history rows are narrow:

```text
fault pair: steering_fault -> front_lateral_authority_drop
seed: 99004
steps: 28, 32
normal margins: 3.497476, 2.771529
wrong margins: 3.483328, 2.757596
history margin gaps: 0.014148, 0.013933
success_drop: false
wrong_history_action_critical: true
```

These rows are useful signal, but not proof-positive. They are one seed, one
fault-family pair, one severity pair, and margin-gap rather than collision
success-drop rows.

## Reset-Only Signal

M990 also finds:

```text
reset_only_rows: 132
reset_history_action_critical_rows: 132
```

This is materially stronger than M984-M987, where wrong histories stayed
successful and accepted rows were zero. However, reset-only sensitivity remains
weaker evidence than wrong-history outcome sensitivity because reset can be a
generic recurrent-state disruption.

## Fault-Pair Coverage

The smoke evaluates `13` fault-family pair groups with broad matched-pair
coverage. The strongest accepted group is:

```text
steering_fault -> front_lateral_authority_drop:
  rows: 60
  accepted_rows: 2
  reset_only_rows: 4
  unique_seeds: 16
```

Other groups show reset-only rows but no accepted wrong-history rows.

## Claim Boundary

M990 uses current single-track model faults and proxies only.

Current/generated families:

```text
brake_authority_drop
combined_fault
delay_noise_fault
drive_authority_drop
front_lateral_authority_drop
global_mu_drop
mass_cg_shift
rear_lateral_authority_drop
steering_fault
```

Future-only physical claims remain blocked:

```text
true single-wheel puncture/blowout
true single-corner grip collapse
left/right split-mu
stuck single caliper or brake pull
single-wheel brake pressure loss
asymmetric half-shaft or CV failure
open/locked differential failure
per-wheel ABS fault
wheel-speed sensor failure as physical wheel dynamics
corner suspension/toe damage
tire pressure/temperature/wear/delamination dynamics
```

## Interpretation

Supported:

```text
The M974 public-gate base is compatible with the existing hidden fault-event harness.
Capability-step faults produce matched pairs and intervention artifacts without actor/input mutation.
The branch has nonzero wrong-history and substantial reset-only signal.
```

Not supported:

```text
The branch is source-positive.
The current smoke is source-diverse.
The accepted rows justify training, PPO, objective design, or promotion.
The current single-track model supports true per-wheel/asymmetric fault claims.
```

Failure taxonomy:

```text
none
```

The smoke objective passes. Scientific proof remains sparse, so the next step
must be a larger no-training source wave.

## Decision

Admit:

```text
m991-v4-public-base-capability-step-fault-source-wave
```

M991 should increase seed and pair coverage while keeping the same actor
contract and no-training discipline. It should test whether the M990
`steering_fault -> front_lateral_authority_drop` signal repeats and whether
other fault-family pairs become source-positive.

Do not train, PPO, promote, or lower proof thresholds based on M990.

## Artifacts

```text
configs/m990_capability_step_fault_scenarios.json
runs/m990_v4_public_base_capability_step_fault_smoke/summary.json
runs/m990_v4_public_base_capability_step_fault_smoke/scenario_summary.csv
runs/m990_v4_public_base_capability_step_fault_smoke/fault_family_summary.csv
runs/m990_v4_public_base_capability_step_fault_smoke/fault_family_pair_summary.csv
runs/m990_v4_public_base_capability_step_fault_smoke/severity_summary.csv
runs/m990_v4_public_base_capability_step_fault_smoke/severity_pair_summary.csv
runs/m990_v4_public_base_capability_step_fault_smoke/cross_fault_pair_summary.csv
runs/m990_v4_public_base_capability_step_fault_smoke/matched_hidden_condition_pairs.csv
runs/m990_v4_public_base_capability_step_fault_smoke/matched_cross_fault_pairs.csv
runs/m990_v4_public_base_capability_step_fault_smoke/intervention_rollouts.csv
runs/m990_v4_public_base_capability_step_fault_smoke/accepted_rows.csv
runs/m990_v4_public_base_capability_step_fault_smoke/reset_only_rows.csv
runs/m990_v4_public_base_capability_step_fault_smoke/rejected_rows.csv
runs/m990_v4_public_base_capability_step_fault_smoke/model_fidelity_limits.md
```
