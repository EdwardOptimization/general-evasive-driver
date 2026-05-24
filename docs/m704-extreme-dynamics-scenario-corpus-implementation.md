# M704 Extreme Dynamics Scenario Corpus Implementation

## Purpose

M704 implements and runs the no-training extreme hidden-condition scenario
corpus designed in M703.

This milestone is diagnostic-only:

```text
no actor training
no objective actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Implementation

M704 adds:

```text
configs/extreme_hidden_condition_scenarios.json
src/autodrift/extreme_dynamics_scenario_corpus.py
tests/test_extreme_dynamics_scenario_corpus.py
```

The runner:

```text
1. Loads the frozen BC5660 recurrent actor.
2. Runs nominal and faulted scenarios with identical seeds.
3. Applies current-model hidden capability faults without changing observation
   shape.
4. Collects snapshots after warm-up/fault evidence.
5. Matches each fault snapshot to a nominal same-seed visible-state snapshot.
6. Replays normal, wrong_matched_history, and reset_hidden continuations.
7. Writes scenario, pair, rollout, accepted/rejected, and fidelity artifacts.
```

Hidden fault labels are never added to actor observations.

## Fault Families

Current-model generated families:

```text
global_mu_drop
front_lateral_authority_drop
rear_lateral_authority_drop
brake_authority_drop
drive_authority_drop
steering_fault
mass_cg_shift
combined_fault
```

Future-only fidelity-limited families:

```text
single_wheel_grip_collapse
single_wheel_puncture_or_blowout
left_right_split_mu
stuck_caliper_or_single_wheel_brake_pull
true_asymmetric_half_shaft_torque_loss
```

These future-only faults are documented in
`model_fidelity_limits.md` but not generated as if the single-track model could
represent them faithfully.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_hidden_condition_scenarios.json \
  --seed-start 40000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m704_extreme_dynamics_scenario_corpus
```

## Artifacts

```text
runs/m704_extreme_dynamics_scenario_corpus/summary.json
runs/m704_extreme_dynamics_scenario_corpus/scenario_summary.csv
runs/m704_extreme_dynamics_scenario_corpus/fault_family_summary.csv
runs/m704_extreme_dynamics_scenario_corpus/severity_summary.csv
runs/m704_extreme_dynamics_scenario_corpus/snapshot_candidates.csv
runs/m704_extreme_dynamics_scenario_corpus/matched_hidden_condition_pairs.csv
runs/m704_extreme_dynamics_scenario_corpus/intervention_rollouts.csv
runs/m704_extreme_dynamics_scenario_corpus/accepted_rows.csv
runs/m704_extreme_dynamics_scenario_corpus/rejected_rows.csv
runs/m704_extreme_dynamics_scenario_corpus/model_fidelity_limits.md
```

## Result Summary

```text
scenario_count:                      5120
snapshot_count:                     16917
matched_pair_count:                  2048
unmatched_rows:                       191
accepted_rows:                         27
normal_failed_rejected:               609
history_insensitive_rejected:        1412
history_action_critical_rows:          27
wrong_history_action_critical_rows:     0
reset_history_action_critical_rows:    27
unique_accepted_fault_families:          5
unique_accepted_severities:             2
unique_accepted_seeds:                  9
result_class: extreme_reset_sparse
```

Cleanliness:

```text
actor_parameters_changed: false
training_started:         false
ppo_used:                 false
promoted:                 false
```

## Fault-Family Summary

Accepted rows by preferred fault family:

```text
front_lateral_authority_drop: 14
steering_fault:               5
drive_authority_drop:         4
global_mu_drop:               3
brake_authority_drop:         1
combined_fault:               0
mass_cg_shift:                0
rear_lateral_authority_drop:  0
```

By severity:

```text
moderate: 21
severe:    6
```

## Key Interpretation

M704 is the first milestone in this branch that produces any accepted
history-sensitive rows after M701 found zero history-action-critical rows.

However, all accepted rows are reset-history sensitive:

```text
wrong_history_action_critical_rows: 0
reset_history_action_critical_rows: 27
```

That means the evidence is useful but still weak:

```text
supported:
  the recurrent state can matter in extreme hidden-condition scenarios

not yet supported:
  a wrong vehicle/fault history reliably misleads the policy
```

This distinction is important. Reset-hidden degradation says the actor is using
some recurrent information. Wrong-history degradation is the stronger
self-identification claim because it tests whether the policy's belief about
vehicle capability can be causally mis-set by incompatible command-response
history.

## Why Wrong-History May Still Be Empty

M704 pairs faulted snapshots mainly against nominal same-seed histories. That
may be too weak:

```text
nominal history may be close enough to the faulted current state
reset_hidden may be more damaging than nominal wrong-history
fault-vs-nominal may not create the strongest ambiguity
```

The next stronger pairing should compare cross-fault histories:

```text
front_authority_drop history into rear_authority_drop current state
low_mu history into steering_fault current state
brake_fade history into drive_loss current state
moderate fault history into severe fault current state
```

The goal is not to make arbitrary wrong histories fail. The goal is to create
matched visible states where two plausible hidden capability beliefs require
different emergency action.

## Supported Claims

M704 supports:

```text
1. Extreme hidden-condition scenario generation is implemented and writes the
   required no-training artifacts.

2. Current-model hidden capability faults can create recurrent-state-sensitive
   emergency rows.

3. The branch should continue, but not directly to objective training.

4. True single-wheel/asymmetric faults remain future fidelity work, not current
   single-track claims.
```

## Falsified Claims

M704 falsifies:

```text
1. The first extreme hidden-condition corpus is already source-positive.

2. Nominal wrong-history pairing is sufficient to expose wrong-history
   self-ID evidence.

3. Reset-hidden sensitivity alone is enough to admit source-corpus export.
```

M704 does not falsify:

```text
the extreme hidden-condition branch
```

because it produced nonzero reset-sensitive accepted rows and identified a
clear next pairing improvement.

## Failure Taxonomy

Primary:

```text
metric_artifact
```

Reason:

```text
Accepted rows exist, but they are reset-only. Treating them as matched
wrong-history self-ID rows would overclaim the evidence.
```

Secondary:

```text
scenario_sampling_failure
```

Reason:

```text
The current nominal-vs-fault matching did not generate source-positive
wrong-history rows with enough volume or seed diversity.
```

Not classified as:

```text
training_instability:
  no training occurred

contract_violation:
  actor input shape and fields were unchanged

proof_washout:
  actor parameters were unchanged
```

## Decision

M704 passes as an implementation milestone:

```text
extreme_dynamics_scenario_corpus_implementation_passed
```

but fails as source-positive evidence:

```text
extreme_reset_sparse_not_source_positive
```

No source export, objective actor update, PPO, or promotion is admitted.

## Next

M705 should audit M704 before another implementation.

Likely next design:

```text
cross-fault wrong-history pairing and severity ladder refinement
```
