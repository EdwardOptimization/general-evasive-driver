# M787 V4 Asymmetric Residual Gate Audit

## Purpose

M787 audits the M786 high-default asymmetric scalar-gate result before any
further calibration, replay, PPO, or checkpoint promotion.

The question is:

```text
Is M786 alpha 0.15 a strong enough scalar-gate result to continue this branch,
or is it mostly another form of alpha scaling?
```

This milestone is audit-only:

```text
no replay run
no calibrator retraining
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Evidence Summary

M786 result:

```text
result_class: v4_normal_margin_calibration_candidate
candidate_alpha_count: 1
candidate_alphas: [0.15]

positive_rows: 2652
supported_positive_rows: 2640
reconstructed_rows: 2640
metadata_missing_rows: 0
rejected_rows: 12

actor_backbone_changed: false
base_residual_head_changed: false
optimizer_updates_only_calibrator: true
ppo_used: false
promoted: false
```

The implementation is clean. The scientific status is more limited.

## Alpha 0.15 Candidate

M786 alpha `0.15` passes the registered candidate gate:

```text
normal_success_rate: 1.000000
normal_collision_rate: 0.000000
strict_normal_retention_pass: true

intervention_action_gap_mean/p10:
  0.043397 / 0.026649

base intervention_action_gap_mean/p10:
  0.040348 / 0.025782

gap lift:
  0.003049

margin_gap_mean:
  0.031901

active_source_min_margin:
  +0.000028
```

This is a valid limited diagnostic positive. It is not a promotion result.

## Remaining Failure at Alpha 0.2

M786 alpha `0.2` still fails strict normal retention:

```text
normal_success_rate: 0.995455
normal_collision_rate: 0.004545
strict_normal_retention_pass: false
active_source_min_margin: -0.000005
```

All normal collision rows come from the same active source:

```text
seed: 77025
source_index: 12
step: 24
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
```

So M786 did not solve the boundary at the original alpha `0.2`. It found a
narrowly safer calibrated alpha.

## Comparison Against Prior Results

Key rows:

```text
M780 uncalibrated alpha 0.125:
  normal_success/collision: 1.000000 / 0.000000
  intervention_gap_mean: 0.044047
  margin_gap_mean: 0.032352
  active_source_min_margin: +0.000009

M783 scalar gate alpha 0.2:
  normal_success/collision: 1.000000 / 0.000000
  intervention_gap_mean: 0.043298
  margin_gap_mean: 0.031837
  active_source_min_margin: +0.000033

M786 asymmetric gate alpha 0.15:
  normal_success/collision: 1.000000 / 0.000000
  intervention_gap_mean: 0.043397
  margin_gap_mean: 0.031901
  active_source_min_margin: +0.000028
```

Interpretation:

```text
M786 beats M783 on the registered intervention gap threshold, but only
slightly. It improves active-source margin relative to M780 alpha 0.125, but
it does not beat M780 alpha 0.125 on intervention gap or margin gap.
```

This makes M786 a useful feasibility point, not a decisive scalar-gate
breakthrough.

## Gate Semantics

M783 final gate means:

```text
gate_normal_mean: 0.499727
gate_intervention_mean: 0.499986
```

M786 final gate means:

```text
gate_normal_mean: 0.670088
gate_intervention_mean: 0.683384
```

M786 therefore escapes the exact global half-gate behavior, but it does not
achieve the M785 intended behavior:

```text
intended high-default gate: about 0.85
intended active normal max: 0.55
intended intervention floor: 0.80
observed normal/intervention means: about 0.67 / 0.68
```

The branch is still too close to scalar alpha retuning:

```text
all action components are scaled together;
risky normal components cannot be suppressed independently;
useful intervention components cannot be retained independently.
```

That limitation is structural to the scalar gate.

## Supported Claims

M787 supports:

```text
1. M786 is a clean diagnostic positive: the asymmetric gate implementation
   found one alpha that passes strict normal retention and the original gap
   threshold without mutating the actor or residual head.

2. High-default asymmetric gating is better than M783's first objective, but
   the improvement is narrow.

3. The scalar gate is likely capacity-limited for this boundary because it
   cannot separately shape steer/throttle/brake residual components.
```

## Falsified Claims

M787 falsifies:

```text
1. M786 solved the original alpha 0.2 boundary.

2. M786 learned a strong high-default asymmetric intervention-retention gate.

3. M786 is ready for PPO, driver checkpoint promotion, or a public base update.
```

M787 does not prove:

```text
1. Scalar gates are impossible.

2. Vector residual calibration will work.

3. Broad generalization.

4. True four-wheel or per-wheel physical fidelity.
```

## Failure Taxonomy

Primary residual risks:

```text
objective_overfit
behavior_regression
scenario_sampling_failure
```

Reason:

```text
The candidate is tied to a public boundary corpus and a narrow alpha. The
objective improved the threshold result, but the learned gate remains close to
moderate global residual scaling and alpha 0.2 still regresses normal behavior.
```

Not failures:

```text
not contract_violation
not metric_artifact
not private_holdout_contamination
not training_instability
not promotion_gate_failure
```

## Decision

M787 blocks PPO and promotion.

The next blocker should be design-only:

```text
m788-v4-vector-residual-calibration-design
```

Rationale:

```text
Continuing to tune scalar gate coefficients risks local gate-passing. The next
evidence increment should test a more expressive residual calibrator that can
shape action components separately while preserving the same human-view input
contract and frozen base actor/residual invariants.
```

M788 should design, but not run, a vector or structured residual calibration
probe that compares against:

```text
M780 alpha 0.125
M783 alpha 0.2
M786 alpha 0.15
```

PPO, checkpoint promotion, and base actor mutation remain blocked.
