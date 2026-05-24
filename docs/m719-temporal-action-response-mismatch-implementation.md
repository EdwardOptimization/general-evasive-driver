# M719 Temporal Action-Response Mismatch Implementation

## Purpose

M719 implements and runs the no-training temporal command-response mismatch
diagnostic designed in M718.

This milestone is diagnostic-only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Implementation

M719 adds:

```text
src/autodrift/temporal_action_response_mismatch.py
tests/test_temporal_action_response_mismatch.py
```

The runner:

```text
1. Reuses the M715/M716 v2 extreme-fault config.
2. Reruns scenarios in memory so hidden states and environment snapshots are
   available.
3. Matches cross-fault current states using the existing visible-state window.
4. Evaluates normal, reset, cross-fault wrong hidden, delayed hidden, pre-fault
   stale hidden, and command-response mismatch hidden variants.
5. Keeps actor observation unchanged at the current decision step.
6. Writes source rows, per-variant rollouts, critical rows, summaries, and a
   result class.
```

The new temporal variants are hidden-state interventions:

```text
delayed_hidden_5
delayed_hidden_10
delayed_hidden_20
pre_fault_stale_hidden
mismatch_zero_command_history
mismatch_command_shift_1
mismatch_response_delay_5
mismatch_response_delay_10
```

Hidden fault labels are never added to actor observations.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.temporal_action_response_mismatch \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --seed-start 72000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m719_temporal_action_response_mismatch
```

## Artifacts

```text
runs/m719_temporal_action_response_mismatch/summary.json
runs/m719_temporal_action_response_mismatch/source_rows.csv
runs/m719_temporal_action_response_mismatch/intervention_rollouts.csv
runs/m719_temporal_action_response_mismatch/temporal_critical_rows.csv
runs/m719_temporal_action_response_mismatch/variant_summary.csv
runs/m719_temporal_action_response_mismatch/fault_family_summary.csv
runs/m719_temporal_action_response_mismatch/source_pool_summary.csv
runs/m719_temporal_action_response_mismatch/rejected_rows.csv
```

## Result Summary

```text
result_class: temporal_action_only

seed_count: 512
fault_count: 32
scenario_count: 16896
snapshot_count: 72056
matched_pair_count: 4096
unmatched_rows: 12
row_count: 42994

temporal_critical_rows: 3114
temporal_action_critical_rows: 3114
temporal_outcome_critical_rows: 0

reset_action_critical_rows: 3140
reset_outcome_critical_rows: 0

unique_temporal_fault_families: 9
unique_temporal_seeds: 22
normal_history_retention_pass: true

actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

Source pools:

```text
m713_low_alpha_family: 2622
m716_general:          1416
m716_reset_only:         58
```

The run is implementation-clean and no-training, but it is not source-positive
closed-loop evidence because outcome-critical rows are zero.

## Variant Breakdown

Key variant summary:

```text
cross_fault_wrong_hidden:
  action-critical rows: 0
  action distance mean: 0.001505
  action distance max:  0.012664
  margin gap max:       0.000655

reset_hidden:
  action-critical rows: 3140
  outcome-critical rows: 0
  action distance mean: 0.019987
  action distance max:  0.033975
  margin gap max:       0.005486

mismatch_zero_command_history:
  temporal action-critical rows: 3064
  temporal outcome-critical rows: 0
  action distance mean: 0.021019
  action distance max:  0.036131
  margin gap max:       0.006888

delayed_hidden_20:
  temporal action-critical rows: 22
  temporal outcome-critical rows: 0
  action distance max: 0.019839

pre_fault_stale_hidden:
  temporal action-critical rows: 22
  temporal outcome-critical rows: 0
  action distance max: 0.018321

delayed_hidden_10:
  temporal action-critical rows: 3
  temporal outcome-critical rows: 0

mismatch_response_delay_10:
  temporal action-critical rows: 3
  temporal outcome-critical rows: 0

mismatch_command_shift_1:
  temporal action-critical rows: 0
```

Most temporal action-critical rows come from:

```text
mismatch_zero_command_history: 3064 / 3114
```

This is important: the actor is highly sensitive to the previous physical
command fields in recurrent history. That is a real command-response coupling
signal, but the current scenarios do not convert it into clearance or success
differences.

## Interpretation

M719 gives a stronger answer than M716:

```text
The actor does use temporal command-response information at the action level.
```

But it still does not prove:

```text
that temporal history causes better closed-loop avoidance margin;
that wrong/stale history causes collision or recovery failure;
that the current policy has deployable self-identification behavior.
```

The result is action-level positive and outcome-level negative:

```text
temporal action signal: strong
closed-loop outcome signal: absent under current scenarios
```

That means this branch should not go directly to source export, actor update,
PPO, or promotion.

## Supported Claims

M719 supports:

```text
1. Temporal command-response intervention tooling is implemented and executable.

2. Actor observations and checkpoint parameters are unchanged.

3. Previous physical command history is behaviorally important at the action
   head: zeroing command history produces action deltas comparable to reset
   hidden.

4. Cross-fault hidden injection remains action-washed-out, confirming the M716
   result.

5. Delayed and pre-fault stale hidden variants produce sparse action-critical
   rows, but not outcome-critical rows.
```

## Falsified Claims

M719 falsifies:

```text
1. The actor ignores temporal command-response history entirely.

2. Cross-fault wrong hidden is the strongest temporal intervention.

3. Action-level temporal mismatch evidence is enough to claim closed-loop
   self-identification.

4. M719 justifies direct actor update, PPO, source export, or promotion.
```

## Failure Taxonomy

Primary:

```text
metric_artifact
```

Reason:

```text
The action-level temporal signal is strong, but closed-loop margin/success
outcome evidence is absent. Reporting this as self-ID proof would overclaim an
action metric.
```

Not classified as:

```text
training_instability:
  no training occurred.

contract_violation:
  actor observation contract was unchanged.

proof_washout:
  actor parameters were unchanged.
```

## Next Step

M720 should audit `temporal_action_only` before any objective design or training.

The audit should decide whether to:

```text
1. build sharper outcome-critical scenarios around mismatch_zero_command_history;
2. return to M713 actor-head/residual objective design using temporal action
   rows as exact action-level supervision;
3. design a future dynamics-fidelity branch for true asymmetric faults;
4. keep temporal rows as diagnostics only.
```

The immediate next blocker is:

```text
m720-temporal-action-only-audit
```
