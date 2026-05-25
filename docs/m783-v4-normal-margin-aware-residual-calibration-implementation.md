# M783 V4 Normal-Margin-Aware Residual Calibration Implementation

## Purpose

M783 implements and runs the no-PPO normal-margin-aware residual calibration
probe designed by M782.

The question is:

```text
Can a small calibrator around the frozen M761 residual head suppress dangerous
low-margin normal residuals while preserving enough intervention separation?
```

This run is diagnostic only:

```text
base actor frozen
M761 residual head frozen
only calibrator parameters trained
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
  --run-dir runs/m783_v4_normal_margin_calibration \
  --device cpu \
  --epochs 60 \
  --seed 7830 \
  --lr 0.001 \
  --alpha-train 0.2 \
  --alphas 0.0,0.125,0.15,0.2
```

## Tooling Added

M783 adds:

```text
src/autodrift/v4_normal_margin_residual_calibration.py
tests/test_v4_normal_margin_residual_calibration.py
```

The new module:

```text
1. loads the frozen M568 BC actor;
2. loads the frozen M761 residual head;
3. trains a small scalar gate g(feature) in [0, 1];
4. executes action = base_action + alpha * g(feature) * residual_delta;
5. uses terminal margin and source labels only as training-time weights and
   audit metadata;
6. writes closed-loop replay artifacts with actor/residual checksums.
```

## Evidence Summary

Registered result:

```text
result_class: v4_normal_margin_calibration_no_gap_lift

positive_rows: 2652
supported_positive_rows: 2640
reconstructed_rows: 2640
sample_reconstruction_success_rate: 0.995475
metadata_missing_rows: 0
rejected_rows: 12

replay_rows: 21120
objective_rows: 10560

candidate_alpha_count: 0
candidate_alphas: []
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
calibrator_parameter_count: 2113
epochs: 60
seed: 7830
lr: 0.001
alpha_train: 0.2
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

Calibrated alphas:

```text
alpha 0.125:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  intervention_action_gap_mean/p10: 0.042183 / 0.026313
  margin_gap_mean: 0.031067
  closed_loop_gap_pass: false
  normal_margin_calibration_candidate: false

alpha 0.15:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  intervention_action_gap_mean/p10: 0.042554 / 0.026420
  margin_gap_mean: 0.031324
  closed_loop_gap_pass: false
  normal_margin_calibration_candidate: false

alpha 0.2:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  intervention_action_gap_mean/p10: 0.043298 / 0.026634
  margin_gap_mean: 0.031837
  closed_loop_gap_pass: false
  normal_margin_calibration_candidate: false
```

Interpretation:

```text
The calibrator protects normal behavior, but it does not preserve enough
intervention separation to pass the candidate gate.
```

At alpha `0.2`, the intervention action-gap mean improves over base by
`0.002950`, just below the `+0.003` closed-loop gap threshold.

## Active Boundary Source

M783 fixes the M780 active source collision:

```text
seed: 77025
source_index: 12
step: 24
preferred_fault: halfshaft_torque_loss_proxy
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
```

Active source normal margin:

```text
M780 alpha 0.125 reference:
  +0.000009

M783 alpha 0.125:
  +0.000067
  collisions: 0 / 12

M783 alpha 0.15:
  +0.000056
  collisions: 0 / 12

M783 alpha 0.2:
  +0.000033
  collisions: 0 / 12
```

This is a meaningful normal-retention improvement over M780: calibrated alpha
`0.2` now has more active-source margin than uncalibrated alpha `0.125`.

## Calibrator Behavior

Final training metrics:

```text
gate_normal_mean: 0.499727
gate_intervention_mean: 0.499986
calibrated_gap_mean: 0.026294
```

Active source gates:

```text
normal gate: about 0.499707
intervention gate: about 0.499795 to 0.500010
```

Interpretation:

```text
The calibrator mostly learned a global half-gate, not a strongly
context-dependent margin-aware gate.
```

That explains the result:

```text
normal branch: fixed
intervention signal: under-amplified
```

This is a clean negative for the initial gate-only objective, not a tooling
failure.

## Supported Claims

M783 supports:

```text
1. The normal-margin calibration tooling works and preserves actor/residual
   checksum invariants.

2. Training-time terminal margin weighting can suppress low-margin normal
   residual enough to remove the active source collision.

3. A simple scalar gate is too blunt in its current objective: it behaves close
   to global residual downscaling and therefore loses too much intervention
   separation.
```

## Falsified Claims

M783 falsifies:

```text
1. The first gate-only calibration objective is sufficient to produce a
   candidate.

2. Low-margin normal suppression alone is enough; the repair also needs a
   stronger asymmetric intervention-retention term or a more expressive
   calibrator.

3. Alpha 0.2 calibrated by this recipe should proceed to PPO or promotion.
```

M783 does not prove:

```text
1. Driver promotion readiness.

2. PPO safety.

3. Broad generalization.

4. True four-wheel or per-wheel physical fidelity.
```

## Failure Taxonomy

Primary result class:

```text
v4_normal_margin_calibration_no_gap_lift
```

Failure taxonomy:

```text
objective_overfit
```

Reason:

```text
The training objective solved normal retention by learning an almost uniform
half-gate, but this did not meet the closed-loop intervention gap threshold.
```

Residual risks:

```text
scenario_sampling_failure
behavior_regression
```

`behavior_regression` remains a residual risk because stronger calibrator
variants could reintroduce normal collisions. In this specific run, strict
normal retention passed for all tested alphas.

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

M783 admits audit only:

```text
m784-v4-normal-margin-aware-residual-calibration-audit
```

M784 should decide whether to:

```text
1. design an asymmetric gate objective with stronger intervention retention;
2. add more boundary rows before calibration;
3. move from scalar gate to residual-vector calibration;
4. stop the calibration branch if it cannot beat simple alpha scaling.
```

PPO, checkpoint promotion, and base actor mutation remain blocked.
