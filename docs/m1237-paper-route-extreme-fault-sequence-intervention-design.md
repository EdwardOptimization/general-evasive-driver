# M1237 Paper-Route Extreme Fault Sequence Intervention Design

## Summary

M1237 designs the next no-training probe after M1236 repaired normal-history
survivability but found no single hidden-state swap signal.

Decision:

```text
extreme_fault_sequence_intervention_design_admit_probe
```

M1237 keeps the actor contract unchanged and moves from single hidden-state
swaps to sequence-level command-response interventions.

No training, PPO, checkpoint repair, promotion, private holdout, profile tuning,
actor-input expansion, or self-identification claim occurs in M1237.

## Why Sequence Interventions

M1236 achieved the timing repair objective:

```text
normal_surviving_fraction: 0.7213541667
normal_surviving_rows: 554 / 768
```

But it also showed:

```text
accepted_rows: 0
reset_only_rows: 0
wrong_history_action_critical_rows: 0
reset_history_action_critical_rows: 0
result_class: history_insensitive_too_mild
```

That means single hidden-state swaps are too weak or too compatible for the
current source. The next causal test should perturb the recent
command-response evidence window rather than only the decision-time hidden
vector.

## Source Rows

The source file is:

```text
runs/m1236_extreme_fault_timing_repair_smoke/rejected_rows.csv
```

The meaningful subset is:

```text
rejection_reason == history_insensitive_too_mild
```

These rows are normal-history viable under the repaired timing/horizon but
single hidden-swap insensitive. They are exactly the cases where a sequence
intervention can test whether the actor needs a recent command-response window
instead of only the current visible state and a single hidden vector.

M1238 can pass the full rejected file to the existing probe because the probe
reports normal-failed rows separately. The result must still be audited for
normal-failed dominance.

## Existing Probe

Use:

```text
src/autodrift/capability_step_sequence_intervention_probe.py
```

This probe reconstructs trace windows, rolls the recurrent state through
modified observation sequences, and reports:

```text
selected_source_rows.csv
sequence_intervention_rows.csv
accepted_sequence_rows.csv
rejected_sequence_rows.csv
variant_summary.csv
fault_pair_summary.csv
history_length_summary.csv
summary.json
```

## Intervention Variants

The probe separates these variant classes:

Temporal-history variants:

```text
delayed_capability_history
reset_then_warm_history
zero_command_history_window
```

Cross-fault / command-response mismatch variants:

```text
cross_fault_response_window
wrong_commands_preferred_response
wrong_response_preferred_commands
```

The result taxonomy must separate:

```text
sequence_cross_fault_positive
sequence_cross_fault_sparse
sequence_temporal_history_positive
sequence_temporal_history_sparse
sequence_action_only
sequence_no_signal
sequence_normal_failed
```

Cross-fault sequence positives are stronger evidence than temporal-only
positives. Temporal-only positives can still be useful, but they do not by
themselves prove cross-fault self-identification.

## M1238 First Probe

Run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.capability_step_sequence_intervention_probe \
  --checkpoint runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt \
  --config configs/m1236_extreme_fault_timing_repair_smoke.json \
  --source-rows runs/m1236_extreme_fault_timing_repair_smoke/rejected_rows.csv \
  --max-source-rows 384 \
  --per-fault-pair-cap 48 \
  --history-lengths 4,8,12 \
  --max-continuation-steps 18 \
  --min-margin-gap 0.012 \
  --min-sequence-action-l2 0.025 \
  --device auto \
  --run-dir runs/m1238_extreme_fault_sequence_intervention_probe
```

Use the repaired 18-step continuation first. If no signal appears, a later
manifest can test a longer continuation, but M1238 should avoid reintroducing
the M1233 normal-failure problem.

## M1238 Pass Criteria

M1238 should pass as a no-training probe if:

```text
summary.json exists
selected_source_rows > 0
intervention_rows > 0
variant_count >= 6
normal_failed_rows < intervention_rows
actor_parameters_changed == false
training_started == false
ppo_used == false
promoted == false
```

Positive scientific signal is diagnostic, not required for the probe to be
valid. Any positive result must be audited before objective or training work.

## Interpretation Rules

If cross-fault sequence positives appear:

```text
audit source diversity and route to corpus export only if pairs and seeds are
diverse enough
```

If temporal-history positives appear but cross-fault remains zero:

```text
record temporal-history dependence and route to temporal sequence corpus export
only after audit
```

If only action-critical rows appear:

```text
route to terminal-margin-grounded sequence target redesign
```

If no signal appears:

```text
synthesize the branch or change source construction, not PPO
```

If normal-failed rows dominate:

```text
return to timing/horizon repair
```

## Decision

```text
extreme_fault_sequence_intervention_design_admit_probe
```

M1238 is admitted as a bounded no-training sequence intervention probe.
