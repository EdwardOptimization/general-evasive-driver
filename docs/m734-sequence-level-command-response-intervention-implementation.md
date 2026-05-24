# M734 Sequence-Level Command-Response Intervention Implementation

## Purpose

M734 implements and runs the no-training sequence-level intervention runner
designed in M733.

The question is:

```text
Can persistent multi-step command-response history interventions produce
outcome-critical rows where one-step hidden/action interventions did not?
```

This milestone is diagnostic-only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Implementation

M734 adds:

```text
src/autodrift/sequence_command_response_intervention.py
tests/test_sequence_command_response_intervention.py
```

The runner:

```text
1. Loads source-balanced M731 source rows.
2. Reconstructs seed/fault snapshots in memory.
3. Replays normal closed-loop continuation.
4. Applies sequence-level observation/history interventions for H steps.
5. Reports source-balance, action, outcome, sentinel, variant, and horizon
   summaries separately.
```

The intervention changes only the diagnostic observation copy passed to the
actor during replay. It does not add hidden parameters, fault labels, oracle
feasibility, TTC, path errors, or any controller-mode input.

## Commands

Smoke:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.sequence_command_response_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --source-rows runs/m731_source_balanced_boundary_outcome_miner/source_rows.csv \
  --seed-start 72000 \
  --seed-count 16 \
  --max-source-rows 32 \
  --horizons 2,4 \
  --device cpu \
  --run-dir runs/m734_sequence_command_response_intervention_smoke
```

Registered run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.sequence_command_response_intervention \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --source-rows runs/m731_source_balanced_boundary_outcome_miner/source_rows.csv \
  --seed-start 72000 \
  --seed-count 512 \
  --max-source-rows 512 \
  --horizons 2,4,6,8 \
  --device cpu \
  --run-dir runs/m734_sequence_command_response_intervention
```

## Artifacts

```text
runs/m734_sequence_command_response_intervention/summary.json
runs/m734_sequence_command_response_intervention/source_rows.csv
runs/m734_sequence_command_response_intervention/intervention_rollouts.csv
runs/m734_sequence_command_response_intervention/sequence_critical_rows.csv
runs/m734_sequence_command_response_intervention/sentinel_rows.csv
runs/m734_sequence_command_response_intervention/rejected_rows.csv
runs/m734_sequence_command_response_intervention/variant_summary.csv
runs/m734_sequence_command_response_intervention/horizon_summary.csv
runs/m734_sequence_command_response_intervention/fault_family_summary.csv
```

## Result Summary

```text
result_class: sequence_outcome_positive

source_candidate_rows: 512
source_unique_seeds: 236
source_unique_preferred_fault_families: 8
source_unique_fault_family_pairs: 30
source_max_seed_dominance: 0.017578
source_max_preferred_family_dominance: 0.126953
source_sentinel_fraction: 0.099609

horizons: [2, 4, 6, 8]
rollout_rows: 12288

sequence_action_critical_rows: 5262
sequence_outcome_critical_rows: 73
unique_sequence_action_seeds: 236
unique_sequence_outcome_seeds: 28
unique_sequence_outcome_fault_family_pairs: 10
max_sequence_outcome_seed_dominance: 0.082192

sentinel_rows: 1224
sentinel_false_positive_rows: 3
sentinel_false_positive_rate: 0.002451

normal_failed_rejected: 0
normal_history_retention_pass: true
actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

M734 passes the registered source-balance and outcome gates:

```text
sequence_outcome_critical_rows target: >= 20
actual: 73

unique_sequence_outcome_seeds target: >= 10
actual: 28

unique_sequence_outcome_fault_family_pairs target: >= 4
actual: 10

sentinel_false_positive_rate target: <= 0.05
actual: 0.002451
```

## Variant Breakdown

```text
zero_command_obs:
  rows: 2048
  sequence_action_critical_rows: 2046
  sequence_outcome_critical_rows: 67
  prefix_l2_mean: 0.042139
  margin_gap_p95: 0.016214
  margin_gap_max: 0.062282

reset_hidden_each_step:
  rows: 2048
  sequence_action_critical_rows: 2047
  sequence_outcome_critical_rows: 6
  prefix_l2_mean: 0.024884
  margin_gap_p95: 0.007167
  margin_gap_max: 0.029036

command_shift_obs:
  rows: 2048
  sequence_action_critical_rows: 769
  sequence_outcome_critical_rows: 0

reset_hidden_then_normal:
  rows: 2048
  sequence_action_critical_rows: 393
  sequence_outcome_critical_rows: 0

response_delay_obs:
  rows: 2048
  sequence_action_critical_rows: 7
  sequence_outcome_critical_rows: 0
```

## Horizon Breakdown

```text
horizon 2:
  sequence_action_critical_rows: 1887
  sequence_outcome_critical_rows: 0

horizon 4:
  sequence_action_critical_rows: 1307
  sequence_outcome_critical_rows: 9

horizon 6:
  sequence_action_critical_rows: 1036
  sequence_outcome_critical_rows: 26

horizon 8:
  sequence_action_critical_rows: 1032
  sequence_outcome_critical_rows: 38
```

Outcome rows appear only at horizons `4`, `6`, and `8`, with the strongest
effect at `8`. This directly supports the M733 hypothesis that one-step
interventions were being repaired by subsequent closed-loop feedback.

## Outcome Distribution

Outcome-critical variants:

```text
zero_command_obs: 67
reset_hidden_each_step: 6
```

Top outcome fault-family pairs:

```text
front_lateral_authority_drop->steering_fault: 15
combined_fault->front_lateral_authority_drop: 11
mass_cg_shift->brake_authority_drop: 10
mass_cg_shift->combined_fault: 9
front_lateral_authority_drop->front_lateral_authority_drop: 9
front_lateral_authority_drop->combined_fault: 6
delay_noise_fault->steering_fault: 5
drive_authority_drop->drive_authority_drop: 4
global_mu_drop->steering_fault: 2
combined_fault->global_mu_drop: 2
```

Sentinel outcome rows:

```text
3 / 1224
false-positive rate: 0.002451
```

The false-positive rate is below threshold, but M735 should still inspect the
sentinel rows before using this corpus for any objective design.

## Interpretation

M734 is the first source-balanced positive outcome result in this branch.

It supports:

```text
The actor's command-response history dependence is not merely action-level.
When command history is corrupted over a short sequence, the resulting
closed-loop trajectory can lose clearance or fail.
```

It also explains why M728/M731 were mostly action-only:

```text
single-step interventions were often corrected by later closed-loop feedback.
Persistent sequence-level interventions expose the outcome dependence.
```

This is still not a trained driver improvement and not a promotion result. It
is a diagnostic intervention result. Source export, objective design, PPO, and
checkpoint promotion require M735 audit first.

## Supported Claims

M734 supports:

```text
1. Source-balanced sequence-level command-response intervention can produce
   outcome-critical rows.

2. The strongest outcome signal is sustained loss of previous-command
   observation, not a one-step reset.

3. Outcome sensitivity grows with intervention horizon.

4. The actor/input contract remains clean and actor parameters are unchanged.
```

## Falsified Claims

M734 falsifies:

```text
1. The action-to-outcome blocker requires immediate dynamics-fidelity work.

2. The current actor's command-history dependence is only a one-step action
   artifact.

3. One-step boundary mining negativity proves no closed-loop self-ID signal.
```

M734 does not prove:

```text
1. PPO can improve the driver without washing out proof.

2. The corpus is ready for training or source export.

3. The learned driver is deployment-ready.
```

## Failure Taxonomy

Primary:

```text
none
```

Reason:

```text
The no-training diagnostic passed the pre-registered source-balance,
sequence-outcome, sentinel, and actor-checksum gates.
```

## Next Step

M735 should audit the M734 positive result before any corpus export or
objective design.

The audit should inspect:

```text
1. whether sentinel false positives are harmless;
2. whether outcome rows are source-diverse and not dominated by a small
   failure mode;
3. whether zero_command_obs is a valid diagnostic for command-response history
   dependence;
4. whether the next step should be compact corpus export, sequence-preference
   objective design, or a repeat/holdout validation.
```
