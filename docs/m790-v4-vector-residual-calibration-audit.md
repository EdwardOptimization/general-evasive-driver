# M790 V4 Vector Residual Calibration Audit

## Purpose

M790 audits the M789 vector residual calibration result before any further
calibration, replay, PPO, or checkpoint promotion.

The question is:

```text
Did the vector output add component-selective residual control, or did it
collapse into another scalar gate?
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

M789 result:

```text
result_class: v4_vector_residual_calibration_component_collapse

positive_rows: 2652
supported_positive_rows: 2640
reconstructed_rows: 2640
metadata_missing_rows: 0
rejected_rows: 12

candidate_alpha_count: 0
strong_candidate_alpha_count: 0
limited_candidate_alpha_count: 0

actor_backbone_changed: false
base_residual_head_changed: false
optimizer_updates_only_calibrator: true
ppo_used: false
promoted: false
```

The implementation is clean. The negative result is scientific, not a tooling
artifact.

## Alpha Result

M789 alpha `0.15`:

```text
normal_success/collision: 1.000000 / 0.000000
intervention_gap_mean/p10: 0.043403 / 0.026651
margin_gap_mean: 0.031905
active_source_min_margin: +0.000027881
vector_pareto_gap_pass: true
vector_pareto_margin_pass: false
vector_limited_candidate: false
```

M789 alpha `0.2`:

```text
normal_success/collision: 0.995455 / 0.004545
intervention_gap_mean/p10: 0.044438 / 0.026958
margin_gap_mean: 0.032615
active_source_min_margin: -0.000005
vector_strong_candidate: false
```

The alpha `0.2` failure remains the same active source:

```text
seed: 77025
source_index: 12
step: 24
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
```

## Comparison To M786

M786 alpha `0.15`:

```text
intervention_gap_mean: 0.043397390743
active_source_min_margin: +0.000028245983
```

M789 alpha `0.15`:

```text
intervention_gap_mean: 0.043402736359
active_source_min_margin: +0.000027881132
```

M789 gains only about `5e-6` in gap mean and loses about `3.6e-7` in active
margin. That is not a meaningful Pareto improvement.

## Component Collapse

M789 final training metrics:

```text
gate_normal_mean: 0.671216
gate_intervention_mean: 0.684845
gate_component_std_mean: 0.000066
```

Final normal component gates:

```text
steer:    0.671292
throttle: 0.671167
brake:    0.671190
```

Final intervention component gates:

```text
steer:    0.684914
throttle: 0.684800
brake:    0.684820
```

This is scalar-like behavior despite the 3-output architecture. The output
dimension alone did not create component-level reasoning.

## Interpretation

M789 likely failed because the objective did not tell the calibrator which
action component is responsible for the active-source normal collision or the
intervention benefit. Without component attribution, the easiest solution is
still a shared moderate residual scale.

The right next step is not to tune coefficients blindly. First identify the
closed-loop role of each M761 residual component:

```text
steer residual
throttle residual
brake residual
steer+brake
steer+throttle
throttle+brake
all residual
no residual
```

Only after that should another vector objective be designed.

## Supported Claims

M790 supports:

```text
1. M789 is a clean negative: implementation and invariants are sound.

2. The M788 vector objective is insufficient because the learned 3-output gate
   collapses to near-identical component values.

3. The active source remains the binding alpha 0.2 normal-retention failure.

4. Further vector calibration needs component sensitivity evidence, not only
   more loss coefficients.
```

## Falsified Claims

M790 falsifies:

```text
1. Vector output dimension alone proves component-selective residual control.

2. M789 beat M786 alpha 0.15.

3. M789 made alpha 0.2 safe.

4. M789 is ready for PPO or promotion.
```

M790 does not prove:

```text
1. Component-selective calibration is impossible.

2. The M761 residual head is unusable.

3. Broad generalization.

4. True four-wheel or per-wheel physical fidelity.
```

## Failure Taxonomy

Primary failure:

```text
objective_overfit
```

Reason:

```text
The objective found a low-loss scalar-like vector gate that matches the old
scalar frontier but does not add the intended component selectivity.
```

Residual risks:

```text
behavior_regression
scenario_sampling_failure
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

M790 blocks PPO and promotion.

The next blocker should be design-only:

```text
m791-v4-residual-component-sensitivity-design
```

M791 should design an audit-only closed-loop component sensitivity probe. It
should not train. Its purpose is to answer which residual components create:

```text
1. active-source normal collision risk;
2. intervention action-gap lift;
3. margin-gap lift;
4. wrong-history sensitivity retention.
```

This evidence is needed before another vector objective is justified.
