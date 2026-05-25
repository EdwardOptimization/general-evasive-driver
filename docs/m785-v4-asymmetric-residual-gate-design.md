# M785 V4 Asymmetric Residual Gate Design

## Purpose

M785 designs the next calibration probe after M784 audited M783 as a clean
no-gap-lift result.

The question is:

```text
Can a high-default asymmetric gate preserve intervention-sensitive residual
signal while still suppressing low-margin normal residuals?
```

This milestone is design-only:

```text
no calibrator training
no replay run
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Why M783 Failed

M783 learned:

```text
gate_normal_mean: 0.499727
gate_intervention_mean: 0.499986
```

That solved normal retention but mostly behaved like global alpha reduction:

```text
M783 alpha 0.2:
  normal_success_rate: 1.0
  normal_collision_rate: 0.0
  intervention_action_gap_mean: 0.043298

base gap mean:
  0.040348

required lift:
  +0.003

actual lift:
  +0.002950
```

The miss is numerically small, but the gate semantics are wrong. The calibrator
did not learn:

```text
normal low-margin branch -> suppress residual
intervention/outcome-critical branch -> keep residual active
```

It learned:

```text
all branches -> half residual
```

M785 therefore changes the objective, not the gate threshold.

## Design Principle

The next probe should make residual retention the default:

```text
default gate: high
exception: low-margin normal rows receive suppression pressure
```

This is the opposite of M783's effective solution.

Deploy-time inputs still stay clean:

```text
gate input = same deployable actor feature used by M761 residual head
```

Training-time only signals:

```text
normal terminal margin
source id
fault family
intervention variant
outcome-critical label
hard-negative availability
```

These signals may weight losses and produce audit tables. They must not enter
the actor, residual head, or gate as deploy-time inputs.

## Model

Keep the same architecture class as M783, with different initialization and
losses:

```text
base actor:
  frozen M568 BC actor

base residual:
  frozen M761 residual head

gate:
  scalar g(feature) in [0, 1]
  feature input is deployable actor feature
```

Executed action:

```text
action = base_action + alpha * g(feature) * delta_m761(feature)
```

M786 should initialize the gate high:

```text
final gate bias: logit(0.85)
final gate weights: zero
initial g: about 0.85
```

This makes M786 test whether the gate can selectively suppress risky normal
branches, rather than whether it can climb out of a 0.5 default.

## Objective Terms

M786 should train only gate parameters.

### 1. Low-Margin Normal Suppression

Only low-margin normal rows should receive strong suppression.

Define:

```text
low_margin_weight =
  clip((m_cutoff - normal_margin_base) / m_cutoff, 0, 1) ** 2
```

Initial:

```text
m_cutoff: 0.001
```

Loss:

```text
L_low_margin_normal =
  low_margin_weight * ||g_n * delta_n||^2
```

This differs from M783: high-margin normal rows should not all be pulled toward
low gate.

### 2. High Default Gate Prior

Keep the gate high on non-low-margin normal rows and intervention rows:

```text
L_high_default_normal =
  (1 - low_margin_weight) * relu(g_default - g_n)^2

L_high_default_intervention =
  relu(g_default - g_i)^2
```

Initial:

```text
g_default: 0.85
```

Purpose:

```text
prevent the global half-gate solution from M783.
```

### 3. Active Boundary Normal Guard

For the known active source:

```text
seed: 77025
source_index: 12
step: 24
```

Require low normal gate:

```text
L_active_normal =
  relu(g_n - g_active_normal_max)^2
```

Initial:

```text
g_active_normal_max: 0.55
```

Rationale:

```text
M783's roughly 0.5 gate made alpha 0.2 safe on the active source.
```

### 4. Active/Outcome Intervention Retention

For outcome-critical intervention rows, especially the active source's
interventions:

```text
L_intervention_gate =
  relu(g_intervention_min - g_i)^2
```

Initial:

```text
g_intervention_min: 0.80
```

This is the main asymmetric change versus M783.

### 5. Gate Contrast on Low-Margin Pairs

For low-margin normal rows paired with outcome-critical intervention rows:

```text
L_gate_contrast =
  low_margin_weight * relu(g_margin - (g_i - g_n))^2
```

Initial:

```text
g_margin: 0.20
```

Purpose:

```text
teach the gate that "same visible scene but corrupted history" should not get
the same residual scaling as the protected normal branch.
```

### 6. Closed-Loop Gap Retention Proxy

Retain the original M783 candidate threshold. Do not weaken it.

Training proxy:

```text
gap_calibrated =
  ||(a_i + alpha_train * g_i * delta_i)
    - (a_n + alpha_train * g_n * delta_n)||

target_gap =
  max(base_gap + 0.003, M780_alpha_0125_gap_if_available)
```

Initial:

```text
alpha_train: 0.2
gap_lift_target: 0.003
```

Loss:

```text
L_gap =
  outcome_weight * relu(target_gap - gap_calibrated)^2
```

### 7. Optional Hard-Negative Calibration

Use hard negatives only when available:

```text
L_hard_negative =
  hard_available * relu(hard_gap - gap_calibrated + 0.005)^2
```

Do not drop positives without hard negatives.

## Total Loss

Initial M786 loss:

```text
L =
  2.0 * L_low_margin_normal
+ 0.25 * L_high_default_normal
+ 1.0 * L_high_default_intervention
+ 4.0 * L_active_normal
+ 2.0 * L_intervention_gate
+ 2.0 * L_gate_contrast
+ 1.0 * L_gap
+ 0.10 * L_hard_negative
+ 1e-4 * L2
```

This is intentionally asymmetric. The desired outcome is not low residual
everywhere. It is:

```text
normal low-margin branch: lower gate
outcome-critical intervention branch: high gate
most other branches: high default gate
```

## Evaluation

M786 should evaluate:

```text
alpha:
  0.0
  0.125
  0.15
  0.2
```

Primary comparison:

```text
M780 uncalibrated alpha 0.125:
  normal success: 1.0
  active source margin: +0.000009
  intervention gap mean: 0.044047

M783 calibrated alpha 0.2:
  normal success: 1.0
  active source margin: +0.000033
  intervention gap mean: 0.043298

M786 target:
  normal success: 1.0
  active source margin >= +0.000009
  intervention gap mean >= 0.044047
```

Strong result:

```text
calibrated alpha 0.2 satisfies strict normal retention
and has intervention gap mean >= M780 alpha 0.125.
```

Minimum candidate result:

```text
some calibrated alpha satisfies:
  strict normal retention
  active source margin >= M780 alpha 0.125
  closed_loop_gap_pass under the original threshold
```

No promotion follows from either result. M786 remains a no-PPO diagnostic.

## Required Diagnostics

M786 must report:

```text
gate_normal_mean / p10 / p90
gate_intervention_mean / p10 / p90
active source normal gate
active source intervention gate
low-margin normal gate statistics
high-margin normal gate statistics
intervention gap and margin gap by alpha
normal collisions by alpha
active source margin by alpha
hard-negative availability
actor checksum before/after
residual-head checksum before/after
```

The audit must explicitly answer:

```text
Did the gate escape global half-scaling?
```

## Stop Conditions

If M786 still learns near-global half scaling:

```text
stop scalar-gate branch or pivot to vector residual calibration.
```

If M786 preserves intervention gap but reintroduces normal collisions:

```text
increase low-margin normal retention or mine more low-margin normal rows.
```

If M786 passes only by using public active source pressure:

```text
keep it diagnostic and require source-diverse boundary mining before any
stronger claim.
```

## Decision

Decision:

```text
asymmetric_gate_design_admit_m786
```

Next blocker:

```text
m786-v4-asymmetric-residual-gate-implementation
```

PPO, checkpoint promotion, and base actor mutation remain blocked.
