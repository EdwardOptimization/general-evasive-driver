# M786 V4 Asymmetric Residual Gate Implementation

## Purpose

M786 implements and runs the no-PPO high-default asymmetric residual gate probe
designed by M785.

The question is:

```text
Can a high-default asymmetric scalar gate escape the M783 global half-gate
solution while keeping the active low-margin normal source safe?
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
  --run-dir runs/m786_v4_asymmetric_residual_gate \
  --device cpu \
  --epochs 60 \
  --seed 7860 \
  --lr 0.001 \
  --alpha-train 0.2 \
  --objective-mode asymmetric_gate \
  --initial-gate 0.85 \
  --gap-lift 0.003 \
  --intervention-gate-floor 0.8 \
  --alphas 0.0,0.125,0.15,0.2
```

## Tooling Changes

M786 extends `src/autodrift/v4_normal_margin_residual_calibration.py` without
changing the default M783 behavior.

Added options:

```text
--objective-mode margin_suppression|asymmetric_gate
--initial-gate
--low-margin-cutoff
--gap-lift
--high-default-gate
--active-normal-gate-max
--intervention-gate-floor
--gate-contrast-margin
```

The new `asymmetric_gate` objective adds:

```text
1. high-default gate initialization;
2. low-margin normal suppression as an exception;
3. high-default normal prior on non-low-margin rows;
4. high-default intervention prior;
5. active-source normal gate upper pressure;
6. intervention gate floor pressure;
7. low-margin normal/intervention gate contrast pressure;
8. unchanged closed-loop gap threshold.
```

Deploy-time inputs remain unchanged:

```text
gate input = deployable actor feature from the frozen actor/residual path
```

Terminal margins and source labels are used only as training-time weights and
audit metadata.

## Evidence Summary

Registered result:

```text
result_class: v4_normal_margin_calibration_candidate

positive_rows: 2652
supported_positive_rows: 2640
reconstructed_rows: 2640
sample_reconstruction_success_rate: 0.995475
metadata_missing_rows: 0
rejected_rows: 12

replay_rows: 21120
objective_rows: 10560

candidate_alpha_count: 1
candidate_alphas: [0.15]
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
seed: 7860
lr: 0.001
alpha_train: 0.2
objective_mode: asymmetric_gate
initial_gate: 0.85
gap_lift: 0.003
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
  intervention_action_gap_mean/p10: 0.042884 / 0.026504
  margin_gap_mean: 0.031547
  closed_loop_gap_pass: false
  normal_margin_calibration_candidate: false

alpha 0.15:
  normal_success_rate: 1.000000
  normal_collision_rate: 0.000000
  intervention_action_gap_mean/p10: 0.043397 / 0.026649
  margin_gap_mean: 0.031901
  closed_loop_gap_pass: true
  normal_margin_calibration_candidate: true

alpha 0.2:
  normal_success_rate: 0.995455
  normal_collision_rate: 0.004545
  intervention_action_gap_mean/p10: 0.044431 / 0.026956
  margin_gap_mean: 0.032610
  closed_loop_gap_pass: true
  strict_normal_retention_pass: false
  normal_margin_calibration_candidate: false
```

Interpretation:

```text
M786 finds a narrow scalar-gate candidate at alpha 0.15. It improves the
intervention action-gap mean over base by 0.003049 while keeping strict normal
retention. Alpha 0.2 still fails normal retention.
```

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
M780 alpha 0.125 reference:
  +0.000009

M786 alpha 0.125:
  +0.000044
  collisions: 0 / 12

M786 alpha 0.15:
  +0.000028
  collisions: 0 / 12

M786 alpha 0.2:
  -0.000005
  collisions: 12 / 12
```

The M786 candidate alpha `0.15` gives about three times the active-source
margin of M780 alpha `0.125`, but the margin is still small in absolute terms.
This is not enough for promotion or PPO.

## Gate Behavior

Final training metrics:

```text
gate_normal_mean: 0.670088
gate_intervention_mean: 0.683384
calibrated_gap_mean: 0.027041
```

Active source gates:

```text
normal first gate: 0.660738
normal mean gate at alpha 0.15: 0.687443
intervention first gates: about 0.668601 to 0.676942
intervention mean gates: about 0.683187 to 0.686322
```

Compared with M783:

```text
M783 gate_normal_mean: 0.499727
M783 gate_intervention_mean: 0.499986
M786 gate_normal_mean: 0.670088
M786 gate_intervention_mean: 0.683384
```

So M786 partially escaped global half-scaling. It did not achieve the intended
high-default `0.85` gate, and it did not create a large normal/intervention
gate separation. The result is better described as:

```text
moderate residual scaling with enough gap at alpha 0.15
```

not:

```text
strong context-dependent asymmetric gating
```

## Supported Claims

M786 supports:

```text
1. The asymmetric gate tooling works and preserves actor/residual checksum
   invariants.

2. High-default asymmetric training improves over M783's global half-gate:
   one alpha now passes both strict normal retention and the original
   intervention gap threshold.

3. The active-source boundary is controllable by gate calibration: alpha 0.15
   remains safe where uncalibrated alpha 0.15 failed in M780.
```

## Falsified Claims

M786 falsifies:

```text
1. The current scalar asymmetric gate makes alpha 0.2 safe.

2. The gate learned the intended high-default 0.85 intervention-retention
   behavior.

3. This result is ready for PPO, checkpoint promotion, or public driver-base
   replacement.
```

M786 does not prove:

```text
1. Broad generalization.

2. PPO safety.

3. True four-wheel or per-wheel physical fidelity.

4. A robust self-ID driver checkpoint.
```

## Failure Taxonomy

Primary result class:

```text
v4_normal_margin_calibration_candidate
```

Residual failure/risk taxonomy:

```text
behavior_regression
scenario_sampling_failure
objective_overfit
```

Reason:

```text
Alpha 0.15 is a valid diagnostic candidate, but alpha 0.2 still collides on
the same active source and the final gate remains closer to moderate global
scaling than to the intended high-default asymmetric policy.
```

Not failures:

```text
not contract_violation
not metric_artifact
not private_holdout_contamination
not training_instability
not proof_washout
```

## Decision

M786 admits audit only:

```text
m787-v4-asymmetric-residual-gate-audit
```

M787 should decide whether the scalar-gate branch should:

```text
1. accept M786 alpha 0.15 as a limited no-PPO diagnostic candidate and run a
   fresh/source-diverse gate audit;
2. strengthen active-source margin pressure and retry scalar gating;
3. pivot from scalar gate to vector residual calibration;
4. stop this calibration branch because it is mostly alpha scaling.
```

PPO, checkpoint promotion, and base actor mutation remain blocked.
