# M1239 Paper-Route Extreme Fault Sequence Negative Audit

## Summary

M1239 audits the M1238 no-signal sequence intervention result.

Decision:

```text
extreme_fault_sequence_negative_audit_route_to_branch_synthesis
```

M1238 is a valid no-training probe, but it is a strong negative for the current
M1236 repaired source path. The next step should be branch synthesis, not
another same-source variant or any training.

No training, PPO, checkpoint repair, promotion, private holdout, profile tuning,
actor-input expansion, or self-identification claim occurs in M1239.

## Evidence Being Audited

M1233:

```text
result_class: cross_fault_reset_only
accepted_rows: 0
reset_only_rows: 58
normal_failed_rejected: 636
```

M1236:

```text
result_class: history_insensitive_too_mild
normal_surviving_fraction: 0.7213541667
accepted_rows: 0
reset_only_rows: 0
history_insensitive_rejected: 554
```

M1238:

```text
result_class: sequence_no_signal
selected_source_rows: 384
intervention_rows: 6912
variant_count: 6
accepted_sequence_rows: 0
sequence_action_critical_rows: 0
normal_failed_rows: 2178
rejected_trace_rows: 0
```

## What The Negative Result Means

M1238 is not a tooling failure:

```text
trace reconstruction succeeded
all six variants ran
normal-failed rows did not dominate
actor checksum stayed unchanged
no training or PPO occurred
```

The variants were simply too weak for this source:

```text
cross_fault_response_window: no signal
delayed_capability_history: no signal
reset_then_warm_history: no signal
wrong_commands_preferred_response: no signal
wrong_response_preferred_commands: no signal
zero_command_history_window: no outcome signal
```

Largest mean action distance:

```text
zero_command_history_window: 0.0020443838
threshold: 0.025
```

So the current source path is not producing behaviorally meaningful
history-necessity evidence.

## Supported Claims

Supported:

```text
The hidden-fault source harness is compatible with the current paper-route L3
checkpoint.

Normal-history survivability can be repaired by timing/horizon/source-window
changes.

For the repaired M1236 source, single hidden-state swaps and sequence-level
command-response interventions are both no-signal under current thresholds.

The workflow correctly blocks training and self-ID claims after no-signal
evidence.
```

## Blocked Or Falsified Claims

Blocked for this source path:

```text
cross-fault wrong-history proof
temporal-history sequence proof
history necessity
recurrent belief
online self-identification
training readiness
promotion
paper-level result
```

Falsified narrow claim:

```text
The M1236 normal-surviving extreme/fault source distribution is sufficient to
expose history dependence via the existing sequence intervention probe.
```

## Same-Source Overfit Risk

Continuing with more small variants on the same M1236 source is now high risk.

Reasons:

```text
M1236 repaired normal survival but removed reset sensitivity.
M1238 tried six sequence variants and three history lengths.
All variants had zero action-critical and zero outcome-critical rows.
No variant showed a near-threshold trend.
```

A longer horizon might increase sensitivity, but it also risks returning to the
M1233 normal-failure regime. That should not be attempted as a casual next run.

## Rejected Next Steps

Do not:

- train from M1236 or M1238;
- run PPO;
- lower action or margin thresholds until positives appear;
- add fault labels or hidden parameters to actor inputs;
- count normal-survival repair as self-identification evidence;
- keep adding same-source intervention variants without branch synthesis.

## Selected Next Route

M1240 should synthesize the full `paper_route_extreme_fault_source_generation`
branch.

The synthesis should decide between:

```text
1. stop this source path and pivot to stronger source construction;
2. design a new source family where hidden dynamics require different actions
   under matched current observations;
3. test a carefully bounded longer-horizon sequence route only if normal
   viability can be preserved;
4. route future physical-fault work to a four-wheel/high-fidelity simulator
   roadmap rather than current single-track proxy claims.
```

The current evidence does not justify training or objective design.

## Decision

```text
extreme_fault_sequence_negative_audit_route_to_branch_synthesis
```

M1240 should be a branch synthesis milestone before any new source mining.
