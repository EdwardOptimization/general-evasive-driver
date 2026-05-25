# M909 V4 Public-Base Residual-Head Probe Implementation

## Purpose

M909 runs the M908 design: train only a new residual head on frozen M399 public
base recurrent actor features.

M909 does not update the actor, run replay, run PPO, or promote a checkpoint.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_sequence_objective_probe \
  --checkpoint runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt \
  --corpus-summary runs/m755_v4_sequence_outcome_corpus_export/summary.json \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --run-dir runs/m909_v4_public_base_residual_head_probe \
  --device cpu \
  --epochs 40 \
  --seed 9090
```

## Result

Artifacts:

```text
runs/m909_v4_public_base_residual_head_probe/summary.json
runs/m909_v4_public_base_residual_head_probe/residual_head.pt
runs/m909_v4_public_base_residual_head_probe/alpha_metrics.csv
runs/m909_v4_public_base_residual_head_probe/objective_rows.csv
runs/m909_v4_public_base_residual_head_probe/training_metrics.csv
runs/m909_v4_public_base_residual_head_probe/rejected_rows.csv
```

Summary:

```text
result_class: v4_sequence_objective_probe_no_gap_lift
checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
positive_rows: 1213
reconstructed_rows: 1213
sample_reconstruction_success_rate: 1.0
metadata_missing_rows: 0
rejected_rows: 0
residual_parameter_count: 8451
candidate_alpha_count: 0
candidate_alphas: []
actor_backbone_changed: false
residual_only_training: true
training_started: true
optimizer_started: true
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Residual head metadata:

```text
feature_dim: 128
max_residual: 0.04
net.0.weight: 64 x 128
net.0.bias: 64
net.2.weight: 3 x 64
net.2.bias: 3
```

Actor checksum:

```text
before: 6942ee9be6ba7c3c65fd56ed7e307cbb82dc8b16bfe5db09b4642de5ce631c1d
after:  6942ee9be6ba7c3c65fd56ed7e307cbb82dc8b16bfe5db09b4642de5ce631c1d
```

## Alpha Metrics

The M399-compatible residual head was generated, but no alpha satisfied both
normal-retention and gap-lift gates.

Key rows:

```text
alpha  normal_retention  gap_lift  exact_candidate  drift_mean  gap_p10   deficit_mean
0.02   true              false     false            0.000205    0.006986  0.016877
0.10   true              false     false            0.001024    0.007314  0.016492
0.20   true              false     false            0.002048    0.007860  0.016010
0.50   false             false     false            0.005121    0.009969  0.014624
1.00   false             false     false            0.010242    0.012391  0.012462
```

Best gap alpha:

```text
alpha: 1.0
normal_anchor_mse_mean: 0.0000537548
first_action_drift_from_base_mean: 0.0102416
normal_intervention_gap_mean: 0.149558
normal_intervention_gap_p10: 0.0123906
gap_deficit_mean: 0.0124621
normal_retention_pass: false
gap_lift_pass: false
exact_probe_candidate: false
```

## Interpretation

M909 is a mixed result:

```text
Compatibility construction succeeded:
  M399 actor loaded;
  rows reconstructed;
  actor unchanged;
  residual head feature_dim is 128.

Objective admissibility failed:
  no alpha passed normal retention and gap-lift together.
```

This is not an input-contract failure and not an actor mutation. It is also not
PPO washout. The likely blocker is objective/target lineage: the M755/M758
sequence residual objective and its hardcoded baseline thresholds were built in
the M568/M761 diagnostic branch, while M399 has a different internal feature
basis and behavior distribution.

Small alphas preserve normal action but do not lift the low-percentile gap.
Large alphas move actions more, but normal retention fails and the p10 gap still
does not reach the registered threshold.

## Supported Claims

M909 supports:

```text
1. A 128-dim residual head can be trained from frozen M399 actor features.
2. The M399 actor remains unchanged during residual-only training.
3. M399 can reconstruct the full M755 sequence objective corpus.
4. The M761-style residual objective does not produce an admissible M399
   residual candidate under the registered gates.
```

## Unsupported Claims

M909 does not support:

```text
M399 residual-head exact candidate;
M880 pair-delta compatibility;
public-base actor update;
replay retention;
PPO safety;
checkpoint promotion.
```

The generated residual head must not be used for replay or M880 exact
compatibility until the no-gap-lift result is audited.

## Decision

Decision:

```text
public_base_residual_head_probe_no_gap_lift_blocked
```

Next:

```text
m910-v4-public-base-residual-head-no-gap-lift-audit
```

M910 should audit whether the right next route is public-base target
regeneration, residual-free objective sanity, or M399-specific sequence
objective recalibration. M910 must not train, replay, run PPO, or promote.
