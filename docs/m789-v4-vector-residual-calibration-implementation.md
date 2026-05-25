# M789 V4 Vector Residual Calibration Implementation

## Purpose

M789 implements and runs the no-PPO per-action-dimension residual calibration
probe designed by M788.

The question is:

```text
Can a vector gate over steer/throttle/brake residual components beat the M786
scalar-gate Pareto point without normal regression?
```

This run is diagnostic only:

```text
base actor frozen
M761 residual head frozen
only vector calibrator parameters trained
no PPO
no checkpoint promotion
```

## Registered Run

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_normal_margin_residual_calibration \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --positive-rows runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --parent-replay-rows runs/m780_v4_broader_normal_boundary_alpha_probe/replay_rows.csv \
  --run-dir runs/m789_v4_vector_residual_calibration \
  --device cpu \
  --epochs 60 \
  --seed 7890 \
  --lr 0.001 \
  --alpha-train 0.2 \
  --objective-mode vector_gate \
  --initial-gate 0.85 \
  --gap-lift 0.003 \
  --intervention-gate-floor 0.8 \
  --alphas 0.0,0.125,0.15,0.2
```

## Tooling Added

M789 extends `src/autodrift/v4_normal_margin_residual_calibration.py` with:

```text
ResidualGate(output_dim=3)
objective_mode: vector_gate
per-component gate logging
vector candidate classification
component-collapse classification
```

The executed action remains:

```text
delta_raw = frozen M761 residual_head(feature)
delta_calibrated = g(feature) * delta_raw
action = frozen_base_action + alpha * delta_calibrated
```

where `g(feature)` is now in `[0, 1]^3` over:

```text
steer
throttle
brake
```

The deploy-time input contract is unchanged: the vector gate receives only the
same deployable actor feature used by the residual head.

## Evidence Summary

Registered result:

```text
result_class: v4_vector_residual_calibration_component_collapse

positive_rows: 2652
supported_positive_rows: 2640
reconstructed_rows: 2640
sample_reconstruction_success_rate: 0.995475
metadata_missing_rows: 0
rejected_rows: 12

replay_rows: 21120
objective_rows: 10560

candidate_alpha_count: 0
strong_candidate_alpha_count: 0
limited_candidate_alpha_count: 0
```

Mutation checks:

```text
actor_backbone_changed: false
base_residual_head_changed: false
optimizer_updates_only_calibrator: true
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Calibrator:

```text
calibrator_parameter_count: 2179
calibrator_output_dim: 3
epochs: 60
seed: 7890
lr: 0.001
objective_mode: vector_gate
```

## Alpha Metrics

Base:

```text
alpha 0.0:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  intervention_action_gap_mean/p10: 0.040348 / 0.025782
  margin_gap_mean: 0.029796
```

Vector-gated alphas:

```text
alpha 0.125:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  intervention_action_gap_mean/p10: 0.042888 / 0.026505
  margin_gap_mean: 0.031550
  active_source_min_margin: +0.000044
  vector_limited_candidate: false

alpha 0.15:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  intervention_action_gap_mean/p10: 0.043403 / 0.026651
  margin_gap_mean: 0.031905
  active_source_min_margin: +0.000028
  vector_pareto_gap_pass: true
  vector_pareto_margin_pass: false
  vector_limited_candidate: false

alpha 0.2:
  normal_success_rate: 0.995455
  normal_collision_rate: 0.004545
  intervention_action_gap_mean/p10: 0.044438 / 0.026958
  margin_gap_mean: 0.032615
  active_source_min_margin: -0.000005
  vector_strong_candidate: false
```

Alpha `0.15` almost reproduces M786's scalar-gate point:

```text
M786 alpha 0.15 gap mean: 0.043397
M789 alpha 0.15 gap mean: 0.043403

M786 alpha 0.15 active margin: +0.000028246
M789 alpha 0.15 active margin: +0.000027881
```

It gains about `5e-6` in gap mean but loses about `3.6e-7` in active margin,
so it is not a Pareto improvement.

## Active Boundary Source

Active source:

```text
seed: 77025
source_index: 12
step: 24
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
```

Active source normal margin:

```text
M789 alpha 0.125:
  +0.000044
  collisions: 0 / 12

M789 alpha 0.15:
  +0.000028
  collisions: 0 / 12

M789 alpha 0.2:
  -0.000005
  collisions: 12 / 12
```

The alpha `0.2` failure is the same active source as M780/M786.

## Component Gate Behavior

Final training metrics:

```text
gate_normal_mean: 0.671216
gate_intervention_mean: 0.684845
gate_component_std_mean: 0.000066
```

Final normal gate components:

```text
steer:    0.671292
throttle: 0.671167
brake:    0.671190
```

Final intervention gate components:

```text
steer:    0.684914
throttle: 0.684800
brake:    0.684820
```

Alpha-level component std is about `5e-5`. This is effectively scalar behavior.
The vector gate has three outputs, but the trained solution does not use them
as distinct action-component controls.

## Supported Claims

M789 supports:

```text
1. The vector calibration tooling works and preserves actor/residual checksum
   invariants.

2. A naive per-action vector gate does not automatically produce component
   selectivity; with the M788 objective it collapses to scalar-like residual
   scaling.

3. The M780/M786 active source remains the binding normal-retention boundary
   at alpha 0.2.
```

## Falsified Claims

M789 falsifies:

```text
1. Simply increasing the gate output dimension from 1 to 3 is enough to beat
   M786.

2. The M788 vector objective can make alpha 0.2 safe without further component
   attribution.

3. M789 is ready for PPO, checkpoint promotion, or public base replacement.
```

M789 does not prove:

```text
1. Vector residual calibration is impossible.

2. Component-selective control is unnecessary.

3. Broad generalization.

4. True four-wheel or per-wheel physical fidelity.
```

## Failure Taxonomy

Primary result class:

```text
v4_vector_residual_calibration_component_collapse
```

Failure taxonomy:

```text
objective_overfit
behavior_regression
scenario_sampling_failure
```

Reason:

```text
The objective found another moderate global-scale solution. It nearly matches
M786 alpha 0.15 but does not Pareto-improve it, and alpha 0.2 still collides on
the active normal source.
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

M789 admits audit only:

```text
m790-v4-vector-residual-calibration-audit
```

M790 should decide whether to:

```text
1. stop the vector-gate branch as local scalar-like gate-passing;
2. run an audit-only residual component sensitivity probe before another
   vector objective;
3. redesign the vector objective with explicit component attribution;
4. return to corpus/architecture evidence instead of more residual calibration.
```

PPO, checkpoint promotion, and base actor mutation remain blocked.
