# M706 Cross-Fault Wrong-History Scenario Design

## Purpose

M706 designs the next no-training implementation after M704/M705.

M704 proved that extreme hidden-condition scenarios can produce reset-sensitive
recurrent-state evidence, but not wrong-history evidence:

```text
accepted_rows:                         27
wrong_history_action_critical_rows:     0
reset_history_action_critical_rows:    27
result_class: extreme_reset_sparse
```

M706 changes the pairing problem:

```text
old:
  faulted current state + nominal wrong history

new:
  faulted current state + incompatible cross-fault wrong history
```

This milestone is design-only:

```text
no implementation
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Design Principle

Wrong-history evidence should be first-class. Reset-hidden evidence remains a
diagnostic, not a source-positive criterion.

Source-positive evidence requires:

```text
normal fault-history rollout succeeds or has positive margin
cross-fault wrong-history rollout degrades margin or success
wrong-history first action or trajectory differs nontrivially
visible current state remains matched
source rows are diverse across fault families, severities, and seeds
```

The actor still sees no fault label.

## Reuse From M704

M707 should reuse the M704 scenario generation logic:

```text
same current-model fault specs
same hidden-label logging only
same actor input contract
same model-fidelity limits
same no-training guardrails
```

But it should change the matching logic:

```text
M704:
  match fault snapshot to nominal snapshot

M707:
  match fault snapshot to another fault snapshot from a contrast family or
  contrast severity
```

Nominal may remain as a diagnostic baseline, but must not be the only wrong
history source.

## Cross-Fault Pairing Matrix

High-priority directed pairs:

```text
preferred current state                 wrong history
---------------------------------------------------------------
front_lateral_authority_drop            rear_lateral_authority_drop
rear_lateral_authority_drop             front_lateral_authority_drop
front_lateral_authority_drop            steering_fault
steering_fault                          front_lateral_authority_drop
global_mu_drop                          brake_authority_drop
brake_authority_drop                    global_mu_drop
global_mu_drop                          steering_fault
steering_fault                          global_mu_drop
brake_authority_drop                    drive_authority_drop
drive_authority_drop                    brake_authority_drop
combined_fault                          single primary component fault
single primary component fault          combined_fault
```

Within-family severity pairs:

```text
moderate global_mu_drop                 severe global_mu_drop
moderate steering_fault                 severe steering_fault
moderate brake_authority_drop           severe brake_authority_drop
moderate front_lateral_authority_drop   severe front_lateral_authority_drop
```

M707 should support a config-driven matrix:

```json
{
  "pairing_rules": [
    {
      "preferred_family": "front_lateral_authority_drop",
      "wrong_family": "rear_lateral_authority_drop",
      "preferred_severities": ["moderate", "severe"],
      "wrong_severities": ["moderate", "severe"]
    }
  ]
}
```

## Severity Ladder Changes

M704 had many reset-sensitive rows from moderate front/steering faults, but no
wrong-history rows. M707 should increase contrast without making preferred rows
normal-failed.

Add or prioritize:

```text
front_authority_severe:
  cf_scale about 0.25-0.35

rear_authority_severe:
  cr_scale about 0.25-0.35

steering_fault_severe:
  max_steer_scale about 0.50-0.60
  max_steer_rate_scale about 0.30-0.40
  steer_tau_scale about 3.0

brake_fade_moderate:
  max_brake_force_scale about 0.65

drive_loss_moderate:
  max_drive_force_scale about 0.45

mu_drop_mild/moderate/severe:
  mu_scale about 0.75, 0.60, 0.42
```

Keep combined faults, but do not let them dominate the accepted set.

## Matching Constraints

Cross-fault matching should remain visible-state constrained:

```text
abs(vx gap) <= 2.0 m/s
abs(vy gap) <= 1.5 m/s
abs(yaw_rate gap) <= 0.5 rad/s
abs(obstacle longitudinal gap) <= 12 m
abs(obstacle lateral gap) <= 2 m
step gap <= 20
```

If matching is empty, M707 should report `matched_state_empty`; it should not
silently relax thresholds after seeing results.

## Acceptance Criteria

Wrong-history source row:

```text
normal_success or normal_margin >= 0.0
wrong_history_margin_gap >= 0.02
  or normal_success and wrong_history_failure
wrong_history_action_l2_gap >= 0.015
```

Reset-only row:

```text
reset_hidden_margin_gap >= 0.02
wrong_history_margin_gap < 0.02
```

Reset-only rows should be written, but not counted as source-positive.

## Result Classes

M707 should classify:

```text
cross_fault_wrong_positive:
  enough wrong-history-critical rows with source diversity

cross_fault_wrong_sparse:
  nonzero wrong-history-critical rows but below source-positive thresholds

cross_fault_reset_only:
  reset-sensitive rows exist but wrong-history-critical rows remain zero

normal_failed_too_severe:
  preferred histories fail before wrong-history comparison is meaningful

history_insensitive_too_mild:
  matched pairs exist but neither wrong nor reset history degrades outcomes

matched_state_empty:
  cross-fault visible-state matching fails

model_fidelity_blocked:
  requested pairings require unsupported four-wheel/asymmetric dynamics
```

Only `cross_fault_wrong_positive` can admit source-corpus export design.

## Source-Positive Thresholds

Initial thresholds:

```text
wrong_history_action_critical_rows >= 30
accepted_rows >= 80
unique_preferred_fault_families >= 4
unique_wrong_fault_families >= 4
unique_severities >= 2
unique_seeds >= 30
max_family_pair_dominance <= 0.35
max_seed_dominance <= 0.08
```

`accepted_rows` should mean wrong-history-critical rows for promotion logic, not
reset-only rows.

## Artifacts

M707 should write:

```text
runs/m707_cross_fault_wrong_history_scenario/
  summary.json
  cross_fault_pair_summary.csv
  fault_family_pair_summary.csv
  severity_pair_summary.csv
  snapshot_candidates.csv
  matched_cross_fault_pairs.csv
  intervention_rollouts.csv
  accepted_rows.csv
  reset_only_rows.csv
  rejected_rows.csv
  model_fidelity_limits.md
```

The summary should include:

```text
wrong_history_action_critical_rows
reset_history_action_critical_rows
wrong_history_source_positive
result_class
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

## Implementation Options

M707 can either:

```text
1. extend extreme_dynamics_scenario_corpus.py with a --pairing-mode
   cross_fault option

2. add a separate module:
   autodrift.cross_fault_wrong_history_scenario
```

Prefer option 1 if the patch remains small, because scenario generation and
fault application are already implemented there. Prefer option 2 if pairing
logic becomes difficult to test in the existing file.

## Negative-Result Interpretation

If `cross_fault_reset_only`:

```text
the actor uses recurrence, but hidden states are not yet specific enough to the
fault type; consider active warm-up/probing or stronger severity contrast
```

If `matched_state_empty`:

```text
cross-fault trajectories diverge too much; use earlier snapshots, broader
matching, or paired initialization
```

If `normal_failed_too_severe`:

```text
reduce severity or increase warm-up/recovery time
```

If `history_insensitive_too_mild`:

```text
increase contrast or move obstacle timing closer to the decision boundary
```

## Decision

M706 admits M707 implementation:

```text
cross_fault_wrong_history_scenario_design_admit_m707
```

Blocked until M707:

```text
source corpus export
objective design
actor update
PPO
checkpoint promotion
```
