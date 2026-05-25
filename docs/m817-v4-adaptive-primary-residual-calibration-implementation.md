# M817 V4 Adaptive Primary Residual Calibration Implementation

## Purpose

M817 implements and runs the source-heldout residual calibration probe designed
in M816.

The question is:

```text
Can a separate residual calibrator be trained and evaluated on the M814
adaptive primary corpus without changing actor or M761 residual-head weights,
without washing out intervention sensitivity, and without PPO or promotion?
```

This milestone is infrastructure-only:

```text
no actor update
no M761 residual-head update
no PPO
no checkpoint promotion
```

M817 trains only a separate residual gate artifact.

## Implementation

New source:

```text
src/autodrift/v4_adaptive_primary_residual_calibration.py
```

New tests:

```text
tests/test_v4_adaptive_primary_residual_calibration.py
```

The implementation adds:

- deterministic source-heldout split by source group / seed / fault-family pair;
- separate scalar residual gate initialized near identity;
- training only on train-split features;
- closed-loop exact train/holdout normal replay;
- closed-loop exact train/holdout intervention replay;
- old-behavior retention proxy through action drift versus M761 alpha `0.2`;
- checksum guards for frozen actor and M761 residual head.

The deployed action equation for this probe is:

```text
action = base_action + alpha * gate_phi(features) * residual_M761(features)
```

with:

```text
alpha: 0.2
initial_gate: 0.999
target_gate: 0.999
calibrator_mode: scalar_gate
```

This is intentionally conservative. It tests whether the calibration harness
can preserve the new M814 corpus and intervention diagnostics before attempting
a more aggressive gate objective.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_adaptive_primary_residual_calibration \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --accepted-rows runs/m814_v4_adaptive_boundary_bracketing/accepted_primary_rows.csv \
  --intervention-rows runs/m814_v4_adaptive_boundary_bracketing/intervention_replay_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --run-dir runs/m817_v4_adaptive_primary_residual_calibration \
  --epochs 20 \
  --device cpu
```

## Result

Run directory:

```text
runs/m817_v4_adaptive_primary_residual_calibration
```

Summary:

```text
result_class: v4_adaptive_primary_residual_calibration_candidate
split_valid: true
train_rows: 57
holdout_rows: 28
snapshot_lookup_rows: 110
missing_snapshots: 0
training_started: true
optimizer_updates_only_calibrator: true
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Split:

```text
train rows: 57
train unique source groups: 37
train unique seeds: 8
train unique fault-family pairs: 8
train unique boundary axes: 3

holdout rows: 28
holdout unique source groups: 18
holdout unique seeds: 9
holdout unique fault-family pairs: 7
holdout unique boundary axes: 3
```

Normal exact replay:

```text
train success_count: 57 / 57
train collision_count: 0
holdout success_count: 28 / 28
holdout collision_count: 0
```

Intervention exact replay:

```text
train baseline_collision_rate: 0.6783625730994152
train calibrated_collision_rate: 0.6783625730994152
holdout baseline_collision_rate: 0.7023809523809523
holdout calibrated_collision_rate: 0.7023809523809523
```

Old-behavior drift proxy:

```text
mean action drift vs M761 alpha 0.2 baseline: 8.148239589147847e-07
max action drift vs M761 alpha 0.2 baseline: 1.5842230141061009e-06
thresholds: mean <= 0.002, max <= 0.02
```

Final gate values stayed near identity:

```text
epoch 20 gate_mean: 0.998985767364502
```

## Contract Checks

The frozen actor and M761 residual head were unchanged:

```text
actor_backbone_changed: false
residual_head_changed: false
```

Checksums:

```text
base_actor_checksum_before: d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
base_actor_checksum_after:  d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
residual_head_checksum_before: 87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
residual_head_checksum_after:  87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
```

Calibrator artifact:

```text
runs/m817_v4_adaptive_primary_residual_calibration/calibrator.pt
```

This is an experiment artifact only. It is not a promoted driver checkpoint.

## Interpretation

M817 is a conservative calibration-harness candidate.

It supports:

- source-heldout split and exact replay evaluation are implemented;
- a separate calibrator can be trained without mutating actor or M761 residual-head weights;
- near-identity calibration preserves M814 train/holdout primary rows;
- intervention collision sensitivity is not washed out under exact replay;
- old behavior is effectively unchanged by this conservative gate.

It does not prove:

- the calibrator improves performance;
- a more aggressive residual gate will be safe;
- PPO should start;
- any checkpoint should be promoted.

## Decision

Classification:

```text
v4_adaptive_primary_residual_calibration_candidate
```

M817 routes to audit only:

```text
m818-v4-adaptive-primary-residual-calibration-audit
```

M818 should decide whether this conservative candidate admits a more aggressive
calibrator objective, a vector-gate ablation, or a source-heldout generalization
check. It must not treat M817 as driver promotion.

## Verification

```text
python -m compileall -q src/autodrift/v4_adaptive_primary_residual_calibration.py tests/test_v4_adaptive_primary_residual_calibration.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_v4_adaptive_primary_residual_calibration.py
```

Result:

```text
3 passed
```
