# M760 V4 Sequence Objective-Only Probe Design

## Purpose

M760 designs a small no-PPO objective-only probe after M759 audited M758 as a
clean exact/offline objective sanity result.

The question is:

```text
Can a tightly gated objective-only probe increase or preserve the
normal-vs-intervention command-response gap while keeping normal-history
behavior effectively unchanged?
```

This milestone is design-only:

```text
no actor update
no optimizer run
no PPO
no checkpoint promotion
no actor-input change
```

## Design Choice

M760 chooses a conservative frozen-backbone residual probe, not direct PPO and
not an unrestricted actor update.

Reason:

```text
M758 proves the objective is reconstructable and non-degenerate, but it does
not prove an actor update can preserve normal behavior. The first coupling step
should therefore train only a small residual head on frozen features, then
evaluate an alpha ladder against exact M758 metrics.
```

The residual probe is not a promoted driver. It is a controlled actor-coupling
experiment.

## Inputs

M761 should use:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m758_v4_sequence_objective_sanity/objective_rows.csv
runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv
configs/extreme_fault_distribution_v4_scenarios.json
```

M761 must reconstruct tensors by replaying source rows as M758 did. The CSVs
are evidence/index data, not complete training tensors.

## Probe Model

Use the frozen BC5660 recurrent actor as a feature provider:

```text
base actor parameters: frozen
residual head input: policy feature or observation/hidden feature already used
                     by the actor, not hidden fault labels
residual head output: delta action in steer/throttle/brake space
executed action: base_action + alpha * bounded_delta
```

Residual constraints:

```text
delta_action is clipped or tanh-bounded
normal-history residual target is zero
intervention-history residual is allowed only to preserve/amplify the existing
normal-vs-intervention direction
```

No hidden dynamics labels may enter the actor input or residual head input.
Fault metadata may only be used for stratified logging and batch balancing.

## Objective Terms

M761 should train the residual head only, with the base actor frozen.

Required terms:

### 1. Normal Zero Residual

```text
L_normal_zero = ||delta_normal||^2
```

Gate purpose:

```text
normal-history behavior should remain unchanged.
```

### 2. Intervention Gap Target

Let:

```text
d_base = a_intervention_base - a_normal_base
direction = normalize(d_base)
target_gap = clamp(prefix_l2_mean_base, 0.02, 0.06)
```

The residual should increase only along the existing intervention direction:

```text
L_gap = relu(target_gap - ||a_intervention_residual - a_normal_residual||)^2
```

If `d_base` is too small or non-finite, skip the row and report it as
degenerate.

### 3. Intervention Anchor

```text
L_intervention_anchor = ||delta_intervention||^2
```

This prevents uncontrolled movement. It should be weaker than `L_gap`.

### 4. Optional Hard-Negative Calibration

If a same-source/same-horizon hard negative exists:

```text
L_hard_negative = relu(action_only_gap - outcome_gap + margin)^2
```

If missing:

```text
skip L_hard_negative and count hard_negative_missing
```

Do not discard positives without hard negatives.

Initial coefficients:

```text
lambda_normal_zero: 2.0
lambda_gap: 1.0
lambda_intervention_anchor: 0.25
lambda_hard_negative: 0.10
```

## Alpha Ladder

M761 should evaluate residual candidates through an alpha ladder:

```text
alpha: 0.02, 0.05, 0.10, 0.20, 0.50, 1.00
```

No alpha is promoted. The output is a diagnostic residual probe artifact.

For each alpha, run exact M758-style metrics:

```text
normal_anchor_mse_mean
normal_anchor_mse_p95
first_action_drift_from_base_mean
first_action_drift_from_base_p95
normal_intervention_gap_mean
normal_intervention_gap_p10
gap_deficit_mean
gap_deficit_p95
hard_negative_available_fraction
source-stratified gap and drift metrics
```

## Pass Criteria

A candidate alpha can be marked `exact_probe_candidate` only if:

```text
sample_reconstruction_success_rate >= 0.98
metadata_missing_rows == 0
normal_anchor_mse_mean <= 0.000004
normal_anchor_mse_p95 <= 0.000025
first_action_drift_from_base_mean <= 0.003
first_action_drift_from_base_p95 <= 0.008
normal_intervention_gap_mean >= base_gap_mean + 0.003
normal_intervention_gap_p10 >= base_gap_p10
gap_deficit_mean <= base_gap_deficit_mean - 0.002
claim_boundary_levels == [current_model_or_proxy]
actor backbone checksum unchanged
optimizer updates only residual head
ppo_used == false
promoted == false
```

Base M758 metrics:

```text
base_gap_mean: 0.024908
base_gap_p10: 0.021141
base_gap_deficit_mean: 0.016809
```

If no alpha passes, the result should be a clean negative, not a failure to
hide.

## Result Classes

M761 should classify the probe as:

```text
v4_sequence_objective_probe_candidate:
  at least one alpha passes exact gates

v4_sequence_objective_probe_normal_drift:
  gap improves but normal behavior drift exceeds gates

v4_sequence_objective_probe_no_gap_lift:
  normal behavior is safe but gap metrics do not improve

v4_sequence_objective_probe_reconstruction_blocked:
  replay/tensor reconstruction fails

v4_sequence_objective_probe_metadata_artifact:
  v4 source or claim-boundary metadata is missing
```

## Implementation Guardrails

M761 must:

```text
freeze base actor parameters;
write residual-only artifacts separately from checkpoints;
record actor backbone checksum before and after;
record residual parameter count;
write exact metrics for every alpha;
write rejected rows and reconstruction failures;
keep hard-negative sparsity visible;
avoid PPO;
avoid checkpoint promotion.
```

M761 must not:

```text
train the base actor directly;
use fault labels as actor/residual inputs;
discard positives without hard negatives;
call a passing alpha a promoted driver;
claim true four-wheel/single-wheel physical-failure coverage.
```

## Registered M761 Shape

M761 should implement a probe command similar to:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v4_sequence_objective_probe \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --corpus-summary runs/m755_v4_sequence_outcome_corpus_export/summary.json \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --run-dir runs/m761_v4_sequence_objective_probe \
  --device cpu \
  --epochs 40 \
  --seed 7610
```

M762 should audit M761 before any direct actor-update, replay gate, PPO, or
promotion branch.
