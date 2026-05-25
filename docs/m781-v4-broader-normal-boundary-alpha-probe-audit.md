# M781 V4 Broader Normal-Boundary Alpha Probe Audit

## Purpose

M781 audits the M780 lower-alpha boundary probe before any repair, residual
retraining, PPO, or checkpoint promotion.

The question is:

```text
Does M780 show a usable lower-alpha feasibility result, and what is the next
blocker?
```

This milestone is audit-only:

```text
no replay run
no actor training
no residual retraining
no optimizer
no PPO
no checkpoint promotion
```

## Evidence Summary

M780 result:

```text
result_class: v4_residual_closed_loop_replay_candidate

positive_rows: 2652
reconstructed_rows: 2640
sample_reconstruction_success_rate: 0.995475
metadata_missing_rows: 0
rejected_rows: 12

candidate_alpha_count: 4
candidate_alphas:
  0.125
  0.15
  0.175
  0.2

actor_backbone_changed: false
optimizer_started: false
training_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

The decisive comparison:

```text
alpha 0.125:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  intervention_action_gap_mean/p10: 0.044047 / 0.026886
  margin_gap_mean: 0.032352
  outcome_sensitivity_retention_rate: 1.000000
  script_closed_loop_replay_candidate: true

base alpha 0.0:
  intervention_action_gap_mean/p10: 0.040348 / 0.025782
  margin_gap_mean: 0.029796

alpha 0.15:
  normal_success_rate: 0.995455
  normal_collision_rate: 0.004545
```

Interpretation:

```text
Alpha 0.125 is a limited lower-alpha feasibility positive.
```

It is the only tested alpha that both:

```text
1. preserves strict normal retention; and
2. passes the script-level closed-loop replay candidate gate.
```

## Boundary Margin Audit

The M777 failing source remains the active constraint:

```text
seed: 77025
source_index: 12
step: 24
preferred_fault: halfshaft_torque_loss_proxy
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
```

Its normal margin by alpha:

```text
alpha 0.0:   +0.000124
alpha 0.05:  +0.000079
alpha 0.10:  +0.000033
alpha 0.125: +0.000009
alpha 0.15:  -0.000014
alpha 0.175: -0.000038
alpha 0.20:  -0.000062
```

This is a clean boundary crossing. Alpha `0.125` passes, but it passes with a
tiny margin:

```text
normal margin at active source: about 9e-6
```

That is not enough slack for a driver-promotion claim. It is enough to show
that the residual direction is not fundamentally unusable on M773.

## What M780 Proves

M780 proves:

```text
1. The M777 alpha 0.2 failure was not broad normal-branch collapse.

2. A lower residual alpha can retain strict normal safety and still improve
   intervention action-gap and margin-gap metrics on the broader M773 corpus.

3. The active constraint is a narrow terminal-margin boundary around one source,
   not a metadata, routing, or actor-contract artifact.
```

M780 does not prove:

```text
1. Alpha 0.125 is robust enough for deployment or promotion.

2. PPO can safely use this residual direction.

3. More alpha sweeps are the right next research branch.

4. The current single-track proxy faults are true four-wheel or per-wheel
   mechanical fault evidence.
```

## Why Not Continue Alpha Sweeps

The current evidence already identifies the scale boundary:

```text
alpha 0.125:
  strict normal retention passes, but active margin is only +9e-6

alpha 0.15:
  same source collides
```

More dense alpha sweeps would only refine the numeric crossing point. That is
not the current scientific blocker. The blocker is now:

```text
How do we keep intervention-sensitive residual corrections while explicitly
protecting low-margin normal branches?
```

This points to residual objective design, not more alpha probing.

## Failure Taxonomy

Primary residual risk:

```text
behavior_regression
```

Reason:

```text
Alpha 0.15 and above still create normal collisions on the active boundary
source. Alpha 0.125 passes but has almost no normal-margin slack.
```

Secondary risk:

```text
scenario_sampling_failure
```

Reason:

```text
M780 is still a current-model/proxy broader corpus result with M773 hard-negative
sparsity and source-concentration caveats.
```

Not failures:

```text
not contract_violation
not metric_artifact
not private_holdout_contamination
not training_instability
not promotion_gate_failure
not proof_washout
```

## Decision

Decision:

```text
promote_to_normal_margin_aware_residual_calibration_design
```

M781 closes the lower-alpha probing branch as a limited feasibility positive
and selects a new design direction:

```text
normal-margin-aware residual calibration / objective repair
```

The next design should preserve the useful intervention-separation signal while
adding explicit protection for low-margin normal rows such as
`seed 77025/source_index 12`. Alpha `0.125` should be kept as a diagnostic
reference, not as a promoted controller.

Next blocker:

```text
m782-v4-normal-margin-aware-residual-calibration-design
```

PPO, checkpoint promotion, residual retraining, and broad generalization claims
remain blocked until the calibration objective is designed and validated.
