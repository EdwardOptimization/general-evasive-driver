# M705 Extreme Dynamics Scenario Corpus Audit

## Purpose

M705 audits the M704 `extreme_reset_sparse` result before any further scenario
implementation, source export, or training.

This milestone is process-only:

```text
no rerun
no source corpus export
no actor update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M704 implementation was clean:

```text
actor_parameters_changed: false
training_started:         false
ppo_used:                 false
promoted:                 false
```

M704 generated:

```text
scenario_count:       5120
snapshot_count:      16917
matched_pair_count:   2048
unmatched_rows:        191
```

Outcome:

```text
accepted_rows:                         27
history_action_critical_rows:          27
wrong_history_action_critical_rows:     0
reset_history_action_critical_rows:    27
result_class: extreme_reset_sparse
```

Accepted fault coverage:

```text
unique_fault_families: 5
unique_severities:    2
unique_seeds:         9
```

Accepted rows by family:

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

The accepted rows are real recurrent-state evidence, but they are not yet the
stronger wrong-history self-identification evidence.

## Supported Claims

M704 supports:

```text
1. Extreme hidden-condition scenario generation is technically viable in the
   current single-track environment.

2. The extreme scenario branch improves over M701: M701 had zero
   history-action-critical rows, while M704 has 27 reset-history-critical rows.

3. The actor's recurrent state affects closed-loop outcome under some extreme
   hidden-condition scenarios.

4. Current-model fault proxies should remain active research assets.

5. True single-wheel/asymmetric faults remain future four-wheel or
   high-fidelity model work.
```

## Falsified Claims

M704 falsifies:

```text
1. The first extreme hidden-condition corpus is already source-positive.

2. Nominal-vs-fault wrong-history pairing is sufficient to produce
   wrong-history self-ID rows.

3. Reset-hidden degradation alone is sufficient to justify source export or
   PPO.
```

M704 does not falsify:

```text
the extreme hidden-condition branch
```

because it produced a positive reset-sensitive signal and identified a sharper
pairing problem.

## Failure Taxonomy Summary

Primary:

```text
metric_artifact
```

Reason:

```text
Accepted rows exist, but all accepted rows are reset-only. Treating them as
wrong-history self-identification evidence would overclaim the metric.
```

Secondary:

```text
scenario_sampling_failure
```

Reason:

```text
The nominal-vs-fault matching strategy did not generate wrong-history-critical
rows.
```

Not classified as:

```text
training_instability:
  no training occurred

contract_violation:
  actor observations were unchanged

proof_washout:
  actor parameters were unchanged
```

## Public Gate Overfit Risk

The current risk is:

```text
reset-hidden gate overfitting
```

Reset-hidden ablations are useful, but a policy can be reset-sensitive without
having a correct vehicle-capability belief. The project should not optimize
only for reset degradation. The stronger evidence remains:

```text
wrong history from an incompatible hidden-condition trajectory produces a
specific wrong maneuver or degraded margin
```

Therefore M706 should preserve reset metrics but optimize the scenario/pairing
design around wrong-history contrast.

## Why Nominal Wrong-History Was Too Weak

M704 matched each faulted snapshot mostly against nominal same-seed history.
This can fail for several reasons:

```text
nominal history may be close enough to many moderate fault histories
nominal hidden may not encode a sharply wrong capability belief
reset_hidden may be more disruptive than nominal wrong-history
same-seed nominal matching may avoid the most ambiguous fault/fault pairs
```

The accepted families point toward useful fault axes:

```text
front_lateral_authority_drop
steering_fault
drive_authority_drop
global_mu_drop
brake_authority_drop
```

The next design should use these families as candidate endpoints for
cross-fault wrong-history pairing.

## Next Branch Decision

Synthesis decision:

```text
continue
```

Continue branch:

```text
extreme_hidden_condition_scenario_generation
```

Next evidence axis:

```text
G_cross_fault_history: replace nominal-only wrong histories with cross-fault
histories that encode incompatible vehicle capability beliefs.
```

M706 should be design-only and should specify:

```text
cross-fault pairing matrix
severity contrast ladder
matched visible-state constraints
wrong-history-specific acceptance gates
reset-only rows as diagnostics, not source-positive evidence
no actor update / PPO / promotion
```

## Candidate Cross-Fault Pairing Matrix

High-priority pairs:

```text
front_lateral_authority_drop <-> rear_lateral_authority_drop
front_lateral_authority_drop <-> steering_fault
global_mu_drop <-> brake_authority_drop
global_mu_drop <-> steering_fault
brake_authority_drop <-> drive_authority_drop
moderate fault <-> severe fault within the same family
```

Lower-priority but useful:

```text
mass_cg_shift <-> steering_fault
rear_lateral_authority_drop <-> drive_authority_drop
combined_fault <-> single primary fault
```

Acceptance should require wrong-history evidence:

```text
wrong_history_action_critical_rows > 0
wrong_history_margin_gap or success_drop passes threshold
wrong_history first-action or trajectory divergence is nontrivial
normal-history remains successful or margin-positive
source diversity across fault families and seeds
```

## Decision

M705 blocks:

```text
source export from M704
objective design
actor update
PPO
checkpoint promotion
```

M705 admits:

```text
m706-cross-fault-wrong-history-scenario-design
```

Decision string:

```text
extreme_reset_sparse_audit_continue_cross_fault_wrong_history_design
```
