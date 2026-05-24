# M717 Extreme-Fault Coverage Refresh Audit

## Purpose

M717 audits the M716 v2 extreme-fault coverage result before any more mining,
objective design, actor update, PPO, or checkpoint promotion.

This milestone is process-only:

```text
no rerun
no source export
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

The coverage branch now has three relevant levels:

```text
M704 nominal-vs-fault extreme corpus:
  scenario_count: 5120
  matched_pair_count: 2048
  reset-history-critical rows: 27
  wrong-history-critical rows: 0
  result_class: extreme_reset_sparse

M707 cross-fault corpus:
  scenario_count: 9728
  matched_pair_count: 2048
  reset-only rows: 15
  wrong-history-critical rows: 0
  result_class: cross_fault_reset_only

M716 v2 full coverage corpus:
  scenario_count: 16896
  snapshot_count: 72056
  matched_pair_count: 4096
  reset-only rows: 58
  wrong-history-critical rows: 0
  result_class: cross_fault_reset_only
```

M716 broadened current-model/proxy coverage across:

```text
global friction
front / rear lateral authority
brake authority
drive authority
steering authority and lag
mass / CG / inertia
actuator delay proxy
combined capability faults
```

It also preserved fidelity boundaries for:

```text
true single-wheel blowout
true split-mu
stuck caliper pull
true asymmetric half-shaft loss
per-wheel brake or ABS faults
corner suspension damage
```

These remain future four-wheel or higher-fidelity dynamics work.

## Key Result

M716 partly validates the user's concern:

```text
More extreme coverage produced more reset-history evidence.
```

But it does not validate the stronger version:

```text
The lack of wrong-history self-ID evidence was only because M704/M707 had too
little current-model fault coverage.
```

The decisive metrics are:

```text
wrong action_l2_gap max:        0.012664
wrong action threshold:         0.015000
wrong history_margin_gap max:   0.000655
history margin threshold:       0.020000

reset action_l2_gap mean:       0.019987
reset margin_gap max:           0.065910
```

So reset hidden is clearly disruptive, but incompatible cross-fault hidden is
still not enough to move deployed actions or margins past the gate.

## Supported Claims

M717 supports:

```text
1. Current-model extreme coverage was not complete before M716.

2. The v2 wave is a stronger coverage test than M704/M707.

3. Within the current single-track/proxy boundary, broader fault coverage alone
   still does not produce source-positive wrong-history self-ID rows.

4. Reset-hidden sensitivity is real and is strongest around front lateral
   authority, steering, and combined puncture/brake-style proxies.

5. Actor update, PPO, source export, and checkpoint promotion remain blocked.
```

## Falsified Claims

M717 falsifies:

```text
1. M704/M707 were negative only because they had too few current-model fault
   families.

2. Another small current-model proxy sweep is the next high-leverage step.

3. Reset-only rows can be reported as matched wrong-history self-ID proof.

4. The v2 single-track proxy corpus justifies immediate training or promotion.
```

M717 does not falsify:

```text
1. True wheel-asymmetric or per-wheel failures may become source-positive under
   a four-wheel or explicit yaw-disturbance dynamics model.

2. Temporal interventions may be more diagnostic than cross-fault hidden swaps.

3. M713 actor-head coupling evidence may still justify a conservative residual
   objective after the temporal intervention audit.
```

## Failure Taxonomy Summary

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
The larger v2 current-model/proxy sampling wave produced no wrong-history
action-critical rows.
```

Secondary:

```text
metric_artifact
```

Reason:

```text
Reset-history degradation is meaningful but would be overclaimed if treated as
wrong-history belief misidentification.
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

## Public Gate Overfit Risk

The current risk is:

```text
reset-only overclaiming
```

The project can now generate many rows where reset hidden hurts action or
margin. Those rows are useful diagnostics, but they are not enough for the core
self-ID claim:

```text
wrong or stale command-response history should induce a wrong vehicle-capability
belief and degrade behavior.
```

Future gates must keep reset-only rows separate from:

```text
wrong-history rows
delayed-history rows
action-response-mismatch rows
source-positive closed-loop outcome rows
```

## Next Branch Decision

Synthesis decision:

```text
pivot
```

Close branch:

```text
extreme_fault_coverage_refresh
```

Next branch:

```text
temporal_action_response_mismatch
```

Reason:

```text
Current-model/proxy coverage expansion has now been tested at a larger scale.
The next most direct way to test command-response self-identification is not
another fault list; it is to intervene on temporal consistency itself.
```

Next evidence axis:

```text
G_temporal_history:
test delayed, stale, and action-response-mismatched histories on M716 reset-only
and M713 low-alpha rows.
```

Next blocker:

```text
m718-temporal-action-response-mismatch-design
```

M718 should design no-training interventions such as:

```text
delayed same-episode hidden state
pre-fault stale hidden after surprise fault activation
history from the same fault family but wrong severity/timing
action-response mismatch histories
reset-hidden sentinel rows
```

The goal is to test whether the actor's belief depends on temporal alignment of
its own commands and sensed response, not merely on swapping one cross-fault
hidden vector into another current observation.

Deferred branches:

```text
actor-head residual objective design from M713
four-wheel or explicit yaw-disturbance dynamics for true asymmetric faults
```

Both remain admissible, but M718 should run first because it is cheaper and
directly targets the command-response-history claim.
