# M782 V4 Normal-Margin-Aware Residual Calibration Design

## Purpose

M782 designs the next repair branch after M781 audited alpha `0.125` as a
limited feasibility positive with too little active margin for promotion.

The question is:

```text
Can we preserve the useful intervention-sensitive residual correction while
explicitly suppressing dangerous residual action on low-margin normal branches?
```

This milestone is design-only:

```text
no residual training
no replay run
no actor update
no optimizer run
no PPO
no checkpoint promotion
```

## Motivation

M780 established the scale boundary:

```text
alpha 0.125:
  normal success: 1.0
  normal collision: 0.0
  intervention action gap mean: 0.044047
  margin gap mean: 0.032352
  active source normal margin: +0.000009

alpha 0.15:
  normal success: 0.995455
  normal collision: 0.004545
  active source normal margin: -0.000014
```

This means the M761 residual direction is useful, but a global alpha is too
crude. It can improve intervention separation, but it does not know when the
normal branch has almost no terminal-margin slack.

The next repair should therefore not be another dense alpha sweep. It should
make the residual correction margin-aware during training while keeping the
deployable input contract clean.

## Actor Contract

The deployable actor contract does not change:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

The calibration branch may use simulator terminal margins, source labels, and
fault metadata only as training-time weights and audit metadata. They must not
be passed as deploy-time actor, residual, or calibrator inputs.

Forbidden deploy-time inputs remain forbidden:

```text
mu
slip
tire force
friction margin
oracle feasibility
TTC
reference trajectory
collision/success/progress labels
normal terminal margin
fault family labels
```

## Proposed Repair Model

M783 should start with the smallest useful repair: a residual gate/calibrator
around the frozen M761 residual head.

Base components:

```text
base actor:
  runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
  frozen

base residual head:
  runs/m761_v4_sequence_objective_probe/residual_head.pt
  frozen for the first calibration probe

calibrator:
  small gate head over the same actor feature used by the residual head
  output scalar gate g in [0, 1]
```

Executed residual action:

```text
delta_base = residual_head(feature)
delta_calibrated = g(feature) * delta_base
action = base_action + alpha * delta_calibrated
```

Why gate first:

```text
1. It preserves the existing learned residual direction.
2. It can suppress residual action on low-margin normal rows.
3. It reduces the risk of inventing a new uncontrolled residual vector.
4. It keeps the base actor and residual head checksums stable.
```

If gate-only cannot preserve intervention signal, a later milestone can design
full residual-head retraining. M782 does not admit that yet.

## Training-Time Data

M783 should use M780/M773 evidence rows:

```text
runs/m780_v4_broader_normal_boundary_alpha_probe/replay_rows.csv
runs/m780_v4_broader_normal_boundary_alpha_probe/objective_rows.csv
runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv
runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv
```

Rows must be reconstructed by replay, as in the previous v4 objective tools.
CSV rows are indices and labels; tensors must come from replayed observations
and recurrent states.

The active low-margin source must be included and upweighted:

```text
seed: 77025
source_index: 12
step: 24
preferred_fault: halfshaft_torque_loss_proxy
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
```

## Objective Terms

M783 should train only the calibrator parameters.

### 1. Low-Margin Normal Suppression

For normal-history rows:

```text
L_normal_margin =
  w_margin(normal_margin_base) * ||g_n * delta_n||^2
```

Suggested weight:

```text
w_margin = 1 + clip(m_ref / max(normal_margin_base, eps), 0, w_max)

m_ref: 0.001
eps: 1e-5
w_max: 50
```

Purpose:

```text
Suppress residual corrections most strongly where the normal branch has little
terminal-margin slack.
```

The terminal margin is a training-time weight. It is not a deploy-time input.

### 2. Boundary Source Guard

Add an explicit source guard term for the M780 active boundary source:

```text
L_boundary_guard =
  w_boundary * ||g_n * delta_n||^2
```

Initial source:

```text
seed 77025 / source_index 12 / step 24
```

This is allowed because it is a training-time corpus weighting rule, not an
actor input. It must be reported as public-corpus repair pressure, not broad
generalization evidence.

### 3. Intervention Signal Retention

For intervention rows, preserve the useful residual separation:

```text
gap_calibrated = ||a_intervention_calibrated - a_normal_calibrated||_2
target_gap = clamp(gap_base + gap_lift, min_gap, max_gap)

L_gap =
  w_outcome * relu(target_gap - gap_calibrated)^2
```

Initial values:

```text
gap_lift: 0.002
min_gap: base gap p10
max_gap: 0.08
```

Purpose:

```text
Do not solve normal retention by zeroing the residual everywhere.
```

### 4. Intervention Gate Floor

For outcome-critical intervention rows:

```text
L_intervention_gate =
  relu(g_min_intervention - g_i)^2
```

Initial value:

```text
g_min_intervention: 0.5
```

This should be weighted modestly and reported carefully. It is not a rule
controller; it is a training objective encouraging the calibrator to keep the
diagnostic residual active on outcome-critical corrupted-history rows.

### 5. Optional Hard-Negative Calibration

Where hard-negative rows are available:

```text
L_hard_negative =
  relu(g_hard_negative - g_intervention + margin)^2
```

If hard negatives are missing:

```text
skip this term and report missing fraction
```

Hard-negative sparsity remains a caveat.

## Total Loss

Initial calibration loss:

```text
L =
  lambda_normal_margin * L_normal_margin
+ lambda_boundary_guard * L_boundary_guard
+ lambda_gap * L_gap
+ lambda_intervention_gate * L_intervention_gate
+ lambda_hard_negative * L_hard_negative_optional
+ lambda_l2 * ||params_calibrator||^2
```

Initial coefficients:

```text
lambda_normal_margin: 2.0
lambda_boundary_guard: 4.0
lambda_gap: 1.0
lambda_intervention_gate: 0.25
lambda_hard_negative: 0.10
lambda_l2: 1e-4
```

M783 may adjust coefficients only as pre-registered config variants. It must
not tune them from closed-loop replay failures and then call the result
unbiased.

## Evaluation Ladder

M783 should evaluate at least:

```text
alpha:
  0.0
  0.125
  0.15
  0.2
```

Primary questions:

```text
1. Can calibrated alpha 0.2 recover strict normal retention?
2. If not, does calibrated alpha 0.125 improve active-source margin over
   M780 alpha 0.125 while preserving intervention gap?
3. Does the calibrator collapse the residual everywhere?
```

## Pass Criteria

A calibration candidate may be marked `normal_margin_calibration_candidate`
only if:

```text
actor_backbone_changed == false
base_residual_head_changed == false
optimizer_updates_only_calibrator == true
ppo_used == false
promoted == false
sample_reconstruction_success_rate >= 0.98
metadata_missing_rows == 0
normal_success_rate == 1.0
normal_collision_rate == 0.0
intervention_action_gap_mean_vs_normal > base_intervention_action_gap_mean
normal_minus_intervention_margin_gap_mean > base_margin_gap_mean
outcome_sensitivity_retention_rate == 1.0
active_source_margin >= M780 alpha 0.125 active_source_margin
```

Stronger success:

```text
calibrated alpha 0.2 passes strict normal retention
and keeps intervention gap above M780 alpha 0.125.
```

If only alpha `0.125` passes, the result is still diagnostic, not promotion.

## Required Artifacts for M783

M783 should write:

```text
runs/m783_v4_normal_margin_calibration/summary.json
runs/m783_v4_normal_margin_calibration/calibration_metrics.csv
runs/m783_v4_normal_margin_calibration/alpha_metrics.csv
runs/m783_v4_normal_margin_calibration/replay_rows.csv
runs/m783_v4_normal_margin_calibration/calibrator.pt
docs/m783-v4-normal-margin-aware-residual-calibration-implementation.md
```

The summary must record checksums for:

```text
base actor before/after
base residual head before/after
calibrator
```

## Supported Claims

M782 supports:

```text
1. The next repair target is objective/calibration design, not more alpha
   search.

2. Normal-margin information may be used as training-time weighting while
   preserving clean deploy-time actor inputs.

3. The first repair should be a small calibrator around the existing residual
   head, not a full actor update or PPO continuation.
```

## Forbidden Claims

M782 does not claim:

```text
1. The calibrator works.

2. Alpha 0.125 is promotable.

3. PPO is safe.

4. The project has true four-wheel or per-wheel fault fidelity.
```

## Decision

Decision:

```text
normal_margin_calibration_design_admit_m783
```

Next blocker:

```text
m783-v4-normal-margin-aware-residual-calibration-implementation
```

PPO, checkpoint promotion, and base actor mutation remain blocked.
